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
    """A single point-in-time reading of the HUD, at `game_clock_seconds` into the game."""

    game_id: str
    frame_path: str
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
