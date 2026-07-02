from lol_scraper.ocr.postprocess import (
    clean_digits,
    parse_clock_seconds,
    parse_gold_thousands,
    parse_int,
)


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


def test_parse_clock_seconds_tolerates_misread_separator():
    # observed real EasyOCR misread of "06:35" — ':' read as '.'
    assert parse_clock_seconds("06.35") == 6 * 60 + 35


def test_parse_gold_thousands_clean_decimal():
    assert parse_gold_thousands("3.3K") == 3300
    assert parse_gold_thousands("12.5K") == 12500


def test_parse_gold_thousands_handles_real_ocr_noise():
    # observed real EasyOCR misreads of "3.3K" / "3.5K" on broadcast HUD digits
    assert parse_gold_thousands("3.36") == 3300  # trailing noise after the decimal digit
    assert parse_gold_thousands("3.31Y") == 3300
    assert parse_gold_thousands("35K &") == 3500  # "K" glyph misread, no decimal point at all
    assert parse_gold_thousands("33K") == 3300


def test_parse_gold_thousands_no_digits():
    assert parse_gold_thousands("garbage") is None
    assert parse_gold_thousands("5") is None
