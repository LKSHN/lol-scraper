"""Converts a raw OCR region dict (as produced by OCRProvider.read_regions) into
a typed GameSnapshot, using the postprocessing helpers to clean up digits.
"""

from lol_scraper.extraction.schemas import GameSnapshot, Team, TeamState
from lol_scraper.ocr.postprocess import parse_clock_seconds, parse_gold_thousands


def parse_snapshot(
    game_id: str,
    frame_path: str,
    ocr_result: dict[str, str],
    blue_team_name: str,
    red_team_name: str,
) -> GameSnapshot:
    return GameSnapshot(
        game_id=game_id,
        frame_path=frame_path,
        game_clock_seconds=parse_clock_seconds(ocr_result.get("game_clock", "")),
        blue=TeamState(
            team=Team(name=blue_team_name, side="blue"),
            gold=parse_gold_thousands(ocr_result.get("blue_team_gold", "")),
        ),
        red=TeamState(
            team=Team(name=red_team_name, side="red"),
            gold=parse_gold_thousands(ocr_result.get("red_team_gold", "")),
        ),
    )
