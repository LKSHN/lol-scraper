from lol_scraper.ocr.postprocess import clean_digits, parse_clock_seconds, parse_int


def test_clean_digits_fixes_common_confusions():
    assert clean_digits("O123I") == "01231"
    assert clean_digits("l2S4B") == "12548"


def test_parse_int():
    assert parse_int("1O234") == 10234
    assert parse_int("S643") == 5643
    assert parse_int("23,450") == 23450
    assert parse_int("abcdefg") is None


def test_parse_clock_seconds():
    assert parse_clock_seconds("23:45") == 23 * 60 + 45
    assert parse_clock_seconds("O5:O9") == 5 * 60 + 9
    assert parse_clock_seconds("garbage") is None
