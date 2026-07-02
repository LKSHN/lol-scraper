from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from lol_scraper.extraction.schemas import GameSnapshot
from lol_scraper.storage import models


def get_or_create_team(session: Session, name: str, league: str | None = None) -> models.Team:
    team = session.get(models.Team, name)
    if team is None:
        team = models.Team(id=name, name=name, league=league)
        session.add(team)
        session.flush()
    return team


def upsert_match(
    session: Session, match_id: str, video_id: str, league: str, title: str
) -> models.Match:
    match = session.get(models.Match, match_id)
    if match is None:
        match = models.Match(id=match_id, video_id=video_id, league=league, title=title)
        session.add(match)
        session.flush()
    return match


def upsert_game(
    session: Session,
    game_id: str,
    match_id: str,
    game_number: int,
    blue_team_name: str,
    red_team_name: str,
    start_seconds: float,
    end_seconds: float,
) -> models.Game:
    blue_team = get_or_create_team(session, blue_team_name)
    red_team = get_or_create_team(session, red_team_name)

    game = session.get(models.Game, game_id)
    if game is None:
        game = models.Game(
            id=game_id,
            match_id=match_id,
            game_number=game_number,
            blue_team_id=blue_team.id,
            red_team_id=red_team.id,
            start_seconds=start_seconds,
            end_seconds=end_seconds,
        )
        session.add(game)
        session.flush()
    return game


def add_snapshot(session: Session, snapshot: GameSnapshot) -> models.Snapshot:
    """Insert a snapshot, or overwrite the existing one for the same (game, video timestamp).

    Re-running the pipeline over a game/window it already processed must not
    duplicate rows -- see the UniqueConstraint on Snapshot. Unlike
    game_clock_seconds (OCR'd, can fail), video_timestamp_seconds is always
    present, so every snapshot can be deduped this way, including ones where
    the clock OCR itself failed.
    """
    values = dict(
        game_id=snapshot.game_id,
        frame_path=snapshot.frame_path,
        video_timestamp_seconds=snapshot.video_timestamp_seconds,
        game_clock_seconds=snapshot.game_clock_seconds,
        blue_gold=snapshot.blue.gold,
        blue_kills=snapshot.blue.kills,
        blue_towers=snapshot.blue.towers,
        red_gold=snapshot.red.gold,
        red_kills=snapshot.red.kills,
        red_towers=snapshot.red.towers,
    )

    stmt = insert(models.Snapshot).values(**values)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_snapshot_game_video_timestamp",
        set_={
            k: v for k, v in values.items() if k not in ("game_id", "video_timestamp_seconds")
        },
    ).returning(models.Snapshot)
    row = session.scalars(stmt).one()
    session.flush()
    return row
