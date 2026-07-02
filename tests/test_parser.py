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
