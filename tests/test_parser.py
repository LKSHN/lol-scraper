from lol_scraper.extraction.parser import parse_snapshot


def test_parse_snapshot_from_fake_ocr_payload():
    # Team gold is shown in broadcast "K" shorthand (e.g. "23.4K"), not plain
    # digits — see ocr/postprocess.parse_gold_thousands.
    ocr_result = {
        "game_clock": "14:32",
        "blue_team_gold": "23.4K",
        "red_team_gold": "21.1K",
    }

    snapshot = parse_snapshot(
        game_id="abc123-g1",
        frame_path="data/frames/abc123/frame_000042.jpg",
        ocr_result=ocr_result,
        blue_team_name="G2 Esports",
        red_team_name="Fnatic",
    )

    assert snapshot.game_id == "abc123-g1"
    assert snapshot.game_clock_seconds == 14 * 60 + 32
    assert snapshot.blue.team.name == "G2 Esports"
    assert snapshot.blue.team.side == "blue"
    assert snapshot.blue.gold == 23400
    assert snapshot.red.team.name == "Fnatic"
    assert snapshot.red.gold == 21100


def test_parse_snapshot_handles_missing_regions():
    snapshot = parse_snapshot(
        game_id="abc123-g1",
        frame_path="frame.jpg",
        ocr_result={},
        blue_team_name="G2 Esports",
        red_team_name="Fnatic",
    )
    assert snapshot.game_clock_seconds is None
    assert snapshot.blue.gold is None
    assert snapshot.red.gold is None


def test_parse_snapshot_rejects_implausible_gold_for_elapsed_time():
    # Reproduces a real EasyOCR misread: "3.6K"-ish gold read as "316" (one
    # stray extra digit) at 1:55 into the game -> parse_gold_thousands alone
    # returns 31600, which is impossible that early -- must be nulled out
    # rather than stored as if it were a real reading.
    ocr_result = {
        "game_clock": "01:55",
        "blue_team_gold": "316",
        "red_team_gold": "3 91",
    }

    snapshot = parse_snapshot(
        game_id="abc123-g1",
        frame_path="frame.jpg",
        ocr_result=ocr_result,
        blue_team_name="G2 Esports",
        red_team_name="Fnatic",
    )

    assert snapshot.game_clock_seconds == 115
    assert snapshot.blue.gold is None
    assert snapshot.red.gold is None


def test_parse_snapshot_keeps_plausible_late_game_gold():
    ocr_result = {"game_clock": "35:00", "blue_team_gold": "45.2K", "red_team_gold": "42.8K"}

    snapshot = parse_snapshot(
        game_id="abc123-g1",
        frame_path="frame.jpg",
        ocr_result=ocr_result,
        blue_team_name="G2 Esports",
        red_team_name="Fnatic",
    )

    assert snapshot.blue.gold == 45200
    assert snapshot.red.gold == 42800
