from lol_scraper.utils.timecodes import seconds_to_timecode, timecode_to_seconds


def test_seconds_to_timecode():
    assert seconds_to_timecode(0) == "00:00:00"
    assert seconds_to_timecode(123) == "00:02:03"
    assert seconds_to_timecode(3661) == "01:01:01"


def test_timecode_to_seconds():
    assert timecode_to_seconds("00:00:00") == 0.0
    assert timecode_to_seconds("00:02:03") == 123.0
    assert timecode_to_seconds("01:01:01") == 3661.0


def test_roundtrip():
    for seconds in (0, 59, 60, 3599, 3600, 7325):
        assert timecode_to_seconds(seconds_to_timecode(seconds)) == float(seconds)
