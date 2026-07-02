from pydantic import BaseModel


class Team(BaseModel):
    name: str
    side: str  # "blue" | "red"


class TeamState(BaseModel):
    team: Team
    gold: int | None = None
    kills: int | None = None
    towers: int | None = None


class GameSnapshot(BaseModel):
    """A single point-in-time reading of the HUD.

    `video_timestamp_seconds` is the frame's offset into the source video --
    known deterministically from the extraction request (start + index *
    interval), not OCR'd, so it's always present and is what identifies a
    snapshot for storage/dedup purposes. `game_clock_seconds` is the OCR'd
    in-game clock reading and can be None if that read failed.
    """

    game_id: str
    frame_path: str
    video_timestamp_seconds: float
    game_clock_seconds: int | None = None
    blue: TeamState
    red: TeamState


class Game(BaseModel):
    game_id: str
    match_id: str
    game_number: int
    blue_team: str
    red_team: str
    start_seconds: float
    end_seconds: float


class Match(BaseModel):
    match_id: str
    video_id: str
    league: str
    title: str
    games: list[Game] = []
