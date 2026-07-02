"""Converts a raw OCR region dict (as produced by OCRProvider.read_regions) into
a typed GameSnapshot, using the postprocessing helpers to clean up digits.
"""

from lol_scraper.extraction.schemas import GameSnapshot, Team, TeamState
from lol_scraper.ocr.postprocess import parse_clock_seconds, parse_gold_thousands

# Plausibility bound for a parsed gold reading, cross-checked against the
# parsed game clock: catches OCR misreads that produce a "valid-looking" but
# impossible value (e.g. reading "316" -> 31600 from what's actually a 2-digit
# "3.6K" plus one stray noise digit -- an absolute cap alone wouldn't catch
# this, since 31600 is a perfectly plausible *late*-game total). Bounds are
# deliberately generous (5 champions x 500 starting gold, plus a very high
# gold/sec ceiling covering passive income + heavy CSing + kills) so real
# values are never rejected, only OCR noise that implies an implausible gain.
#
# When the clock itself didn't parse, gold is rejected outright rather than
# falling back to some absolute cap -- verified on a real full-VOD run that
# during non-gameplay segments (draft, pre-game), the tournament's "26"
# season-branding logo sits in the exact screen position gold occupies during
# live play and gets misread as "2.6K" -> 2600 on dozens of frames, well
# within any plausible-looking absolute cap. Without a valid clock reading
# there's no time context to validate gold against at all, so it can't be
# trusted regardless of its value.
_STARTING_TEAM_GOLD = 2500
_MAX_PLAUSIBLE_GOLD_PER_SECOND = 40


def _is_plausible_gold(gold: int | None, elapsed_seconds: int | None) -> bool:
    if gold is None:
        return True
    if elapsed_seconds is None:
        return False
    if gold < 0:
        return False
    return gold <= _STARTING_TEAM_GOLD + elapsed_seconds * _MAX_PLAUSIBLE_GOLD_PER_SECOND


def parse_snapshot(
    game_id: str,
    frame_path: str,
    video_timestamp_seconds: float,
    ocr_result: dict[str, str],
    blue_team_name: str,
    red_team_name: str,
) -> GameSnapshot:
    game_clock_seconds = parse_clock_seconds(ocr_result.get("game_clock", ""))

    blue_gold = parse_gold_thousands(ocr_result.get("blue_team_gold", ""))
    if not _is_plausible_gold(blue_gold, game_clock_seconds):
        blue_gold = None

    red_gold = parse_gold_thousands(ocr_result.get("red_team_gold", ""))
    if not _is_plausible_gold(red_gold, game_clock_seconds):
        red_gold = None

    return GameSnapshot(
        game_id=game_id,
        frame_path=frame_path,
        video_timestamp_seconds=video_timestamp_seconds,
        game_clock_seconds=game_clock_seconds,
        blue=TeamState(team=Team(name=blue_team_name, side="blue"), gold=blue_gold),
        red=TeamState(team=Team(name=red_team_name, side="red"), gold=red_gold),
    )
