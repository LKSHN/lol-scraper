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
    """Parse a game clock like '23:45' (MM:SS) into total seconds.

    The ':' separator is thin and OCR sometimes reads it as a lookalike (e.g.
    '.') rather than dropping it outright -- any single non-digit is accepted
    between the minute/second digit groups rather than requiring ':' exactly.
    But often the separator isn't misread as *anything*, it's just gone (e.g.
    "12:05" -> "1205", confirmed on real broadcast frames, seemingly on
    motion/scene-change frames where the thin colon dots lose contrast) --
    falls back to treating the last 2 digits of a plain digit run as seconds,
    since the overlay always shows exactly 2 digits there.
    """
    cleaned = clean_digits(raw)

    match = re.search(r"(\d{1,2})\D(\d{2})", cleaned)
    if match:
        minutes, seconds = match.groups()
        return int(minutes) * 60 + int(seconds)

    digits = "".join(re.findall(r"\d", cleaned))
    if len(digits) < 3:
        return None
    minutes, seconds = digits[:-2], digits[-2:]
    return int(minutes) * 60 + int(seconds)


def parse_gold_thousands(raw: str) -> int | None:
    """Parse a team-gold reading shown in broadcast "K" shorthand (e.g. "3.3K" -> 3300).

    OCR on the small, stylized gold digits is unreliable at literally reading
    the "K" glyph or the (tiny) decimal point — in practice it often returns
    something like "33K", "3.31Y", or "330" for what's displayed as "3.3K".
    Rather than depend on spotting a literal "K"/".", this: (1) prefers an
    explicit decimal point if OCR happened to catch one, taking only the
    single digit after it (ignoring any trailing OCR noise); (2) otherwise
    falls back to treating the last digit of the longest digit run as the
    decimal digit, since the broadcast overlay always shows exactly one.
    """
    cleaned = clean_digits(raw)

    decimal_match = re.search(r"(\d+)[.,](\d)", cleaned)
    if decimal_match:
        whole, decimal_digit = decimal_match.groups()
        return round(float(f"{whole}.{decimal_digit}") * 1000)

    # No decimal point survived OCR — stray spaces/junk can also split what's
    # really one number into several digit runs (e.g. "3 31" for "33" + noise),
    # so collect every digit seen rather than just the first run.
    digits = "".join(re.findall(r"\d", cleaned))
    if len(digits) < 2:
        return None
    whole, decimal_digit = digits[:-1], digits[-1]
    return round(float(f"{whole}.{decimal_digit}") * 1000)
