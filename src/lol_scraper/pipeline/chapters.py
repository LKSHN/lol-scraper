"""Detects which of a VOD's YouTube chapters are actual games.

Broadcast VODs typically chapter every segment of the stream -- intro,
pregame show, drafts/bans, each game, post-game analysis, ads -- not just
the games themselves. Every production we've checked (LoL Esports/MSI)
titles game chapters "Game 1", "Game 2", etc., so that's what's matched;
anything else is dropped.
"""

import re

from pydantic import BaseModel

from lol_scraper.ingestion.schemas import Chapter

_GAME_CHAPTER_RE = re.compile(r"\bgame\s*(\d+)\b", re.IGNORECASE)


class NoGameChaptersFoundError(RuntimeError):
    pass


class DetectedGame(BaseModel):
    game_number: int
    start_seconds: float
    end_seconds: float
    title: str


def detect_games(chapters: list[Chapter]) -> list[DetectedGame]:
    """Filter a VOD's chapters down to the ones that are actual games, in order.

    game_number comes from the number in the chapter title, not the
    chapter's position in the list, so a non-game chapter between two games
    (e.g. a caster interview) doesn't throw off numbering.
    """
    games = []
    for chapter in chapters:
        match = _GAME_CHAPTER_RE.search(chapter.title)
        if not match:
            continue
        games.append(
            DetectedGame(
                game_number=int(match.group(1)),
                start_seconds=chapter.start_seconds,
                end_seconds=chapter.end_seconds,
                title=chapter.title,
            )
        )
    games.sort(key=lambda g: g.game_number)
    return games
