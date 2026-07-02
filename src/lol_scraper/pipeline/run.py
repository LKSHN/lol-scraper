"""End-to-end orchestration: ingestion -> frames -> OCR -> parsing -> storage.

Each stage is implemented in its own module (ingestion/, video/, ocr/,
extraction/, storage/) so it can be developed and tested independently. This
module just wires them together, either for one explicit game window
(run_for_video) or for every game auto-detected from the VOD's YouTube
chapters (run_for_match).
"""

from lol_scraper.config import settings
from lol_scraper.extraction.parser import parse_snapshot
from lol_scraper.ingestion.schemas import VideoMetadata
from lol_scraper.ingestion.youtube import fetch_metadata, resolve_stream_url
from lol_scraper.logging_conf import get_logger
from lol_scraper.ocr.base import OCRProvider
from lol_scraper.pipeline.chapters import NoGameChaptersFoundError, detect_games
from lol_scraper.storage import repository
from lol_scraper.storage.db import get_session
from lol_scraper.video.frames import extract_frames
from lol_scraper.video.regions import DEFAULT_REGIONS

logger = get_logger(__name__)


def run_for_video(
    url: str,
    *,
    league: str,
    blue_team_name: str,
    red_team_name: str,
    ocr_provider: OCRProvider,
    game_number: int = 1,
    start_seconds: float = 0.0,
    end_seconds: float | None = None,
) -> None:
    """Runs the full pipeline for one explicit game window within one YouTube video.

    Player-level extraction is left as follow-up work. For auto-splitting a
    VOD into all of its games via YouTube chapters, see run_for_match.
    """
    metadata = fetch_metadata(url)
    logger.info("pipeline.metadata", video_id=metadata.video_id, title=metadata.title)

    stream_url = resolve_stream_url(url)
    _run_game(
        metadata,
        stream_url,
        league=league,
        blue_team_name=blue_team_name,
        red_team_name=red_team_name,
        ocr_provider=ocr_provider,
        game_number=game_number,
        start_seconds=start_seconds,
        end_seconds=end_seconds or metadata.duration_seconds,
    )


def run_for_match(
    url: str,
    *,
    league: str,
    blue_team_name: str,
    red_team_name: str,
    ocr_provider: OCRProvider,
) -> None:
    """Auto-detects every game in a VOD from its YouTube chapters and runs the
    full pipeline for each, in one call.

    blue_team_name/red_team_name are assumed constant across every detected
    game. That's a real simplification: teams swap sides between games in a
    Bo3/Bo5, and chapter titles ("Game 1", "Game 2"...) don't say which side
    played which game, so a side swap isn't detected or corrected here --
    same limitation run_for_video already had for a single game, just not
    yet solved for a multi-game match either. Raises NoGameChaptersFoundError
    if the VOD has no chapters titled like a game (e.g. no chapters at all).
    """
    metadata = fetch_metadata(url)
    logger.info("pipeline.metadata", video_id=metadata.video_id, title=metadata.title)

    games = detect_games(metadata.chapters)
    if not games:
        raise NoGameChaptersFoundError(
            f"No game chapters found on {metadata.video_id} ({len(metadata.chapters)} "
            "chapters total) -- use run_for_video with an explicit --start/--end instead."
        )

    stream_url = resolve_stream_url(url)
    for game in games:
        logger.info(
            "pipeline.match.game_detected",
            game_number=game.game_number,
            title=game.title,
            start=game.start_seconds,
            end=game.end_seconds,
        )
        _run_game(
            metadata,
            stream_url,
            league=league,
            blue_team_name=blue_team_name,
            red_team_name=red_team_name,
            ocr_provider=ocr_provider,
            game_number=game.game_number,
            start_seconds=game.start_seconds,
            end_seconds=game.end_seconds,
        )

    logger.info("pipeline.match.done", video_id=metadata.video_id, game_count=len(games))


def _run_game(
    metadata: VideoMetadata,
    stream_url: str,
    *,
    league: str,
    blue_team_name: str,
    red_team_name: str,
    ocr_provider: OCRProvider,
    game_number: int,
    start_seconds: float,
    end_seconds: float,
) -> None:
    match_id = metadata.video_id
    game_id = f"{match_id}-g{game_number}"

    # Scoped per game_id, not just video_id: extract_frames clears its output
    # dir on every call (see video/frames.py), so if two games from the same
    # VOD shared a directory, processing game 2 would wipe game 1's frames
    # and reuse their filenames (frame_000001.jpg, ...) for entirely
    # different video timestamps -- silently corrupting every frame_path
    # already stored for game 1.
    frames_dir = settings.frames_dir / game_id
    frames = extract_frames(
        stream_url,
        frames_dir,
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        interval_seconds=settings.frame_interval_seconds,
    )

    with get_session() as session:
        repository.upsert_match(session, match_id, metadata.video_id, league, metadata.title)
        repository.upsert_game(
            session,
            game_id,
            match_id,
            game_number,
            blue_team_name,
            red_team_name,
            start_seconds,
            end_seconds,
        )

        # extract_frames samples at a fixed fps=1/interval starting at start_seconds,
        # so each frame's offset into the source video is known directly from its
        # position in the list -- no need to (unreliably) OCR it back out of the HUD.
        for index, frame_path in enumerate(frames):
            video_timestamp_seconds = start_seconds + index * settings.frame_interval_seconds
            ocr_result = ocr_provider.read_regions(frame_path, DEFAULT_REGIONS)
            snapshot = parse_snapshot(
                game_id,
                str(frame_path),
                video_timestamp_seconds,
                ocr_result,
                blue_team_name,
                red_team_name,
            )
            repository.add_snapshot(session, snapshot)

    logger.info("pipeline.done", game_id=game_id, frame_count=len(frames))
