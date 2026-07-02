"""Cleans up raw OCR strings into typed values.

OCR on stylized broadcast fonts commonly confuses similar-looking characters.
`clean_digits` fixes the common letter/digit confusions before parsing ints.
It translates letters unconditionally, so it's only safe on OCR readings of
regions expected to be purely numeric (gold, clock, kill counts) — not on
text that may legitimately contain those letters.
"""

import re

_DIGIT_CORRECTIONS = str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "S": "5", "B": "8"})


def clean_digits(raw: str) -> str:
    return raw.translate(_DIGIT_CORRECTIONS)


def parse_int(raw: str) -> int | None:
    cleaned = clean_digits(raw).replace(",", "").replace(".", "")
    match = re.search(r"-?\d+", cleaned)
    return int(match.group()) if match else None


def parse_clock_seconds(raw: str) -> int | None:
    """Parse a game clock like '23:45' (MM:SS) into total seconds."""
    cleaned = clean_digits(raw)
    match = re.search(r"(\d{1,2}):(\d{2})", cleaned)
    if not match:
        return None
    minutes, seconds = match.groups()
    return int(minutes) * 60 + int(seconds)
