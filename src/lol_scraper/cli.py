import typer

from lol_scraper.config import settings
from lol_scraper.ingestion.youtube import fetch_metadata, resolve_stream_url
from lol_scraper.logging_conf import configure_logging, get_logger
from lol_scraper.video.frames import extract_frames

app = typer.Typer(help="Scrape LoL esports VODs from YouTube and extract structured stats.")
logger = get_logger(__name__)


@app.callback()
def main() -> None:
    configure_logging()


@app.command()
def ingest(url: str) -> None:
    """Fetch and print video metadata + chapters, without downloading anything."""
    metadata = fetch_metadata(url)
    typer.echo(metadata.model_dump_json(indent=2))


@app.command()
def frames(
    url: str,
    start: float = typer.Option(0.0, help="Start offset in seconds"),
    end: float | None = typer.Option(None, help="End offset in seconds"),
    interval: float = typer.Option(
        settings.frame_interval_seconds, help="Seconds between sampled frames"
    ),
) -> None:
    """Debug command: extract sampled frames from a VOD into data/frames/<video_id>/."""
    metadata = fetch_metadata(url)
    stream_url = resolve_stream_url(url)
    out_dir = settings.frames_dir / metadata.video_id
    written = extract_frames(
        stream_url, out_dir, start_seconds=start, end_seconds=end, interval_seconds=interval
    )
    typer.echo(f"Wrote {len(written)} frames to {out_dir}")


@app.command("pipeline-run")
def pipeline_run(
    url: str,
    league: str = typer.Option(..., help="e.g. LEC, LCS"),
    blue_team: str = typer.Option(..., help="Blue side team name"),
    red_team: str = typer.Option(..., help="Red side team name"),
    game_number: int = typer.Option(1),
    start: float = typer.Option(0.0),
    end: float | None = typer.Option(None),
) -> None:
    """Run the full pipeline (ingest -> frames -> OCR -> parse -> store) for one game."""
    from lol_scraper.ocr.easyocr_provider import EasyOCRProvider
    from lol_scraper.pipeline.run import run_for_video

    run_for_video(
        url,
        league=league,
        blue_team_name=blue_team,
        red_team_name=red_team,
        ocr_provider=EasyOCRProvider(),
        game_number=game_number,
        start_seconds=start,
        end_seconds=end,
    )


@app.command("pipeline-run-match")
def pipeline_run_match(
    url: str,
    league: str = typer.Option(..., help="e.g. LEC, LCS"),
    blue_team: str = typer.Option(..., help="Blue side team name (assumed constant across games)"),
    red_team: str = typer.Option(..., help="Red side team name (assumed constant across games)"),
) -> None:
    """Auto-detect every game in a VOD from its YouTube chapters (titled "Game 1",
    "Game 2", ...) and run the full pipeline for each, in one command."""
    from lol_scraper.ocr.easyocr_provider import EasyOCRProvider
    from lol_scraper.pipeline.run import run_for_match

    run_for_match(
        url,
        league=league,
        blue_team_name=blue_team,
        red_team_name=red_team,
        ocr_provider=EasyOCRProvider(),
    )


if __name__ == "__main__":
    app()
