def seconds_to_timecode(total_seconds: float) -> str:
    """123.0 -> '00:02:03'"""
    total = int(total_seconds)
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def timecode_to_seconds(timecode: str) -> float:
    """'00:02:03' -> 123.0"""
    parts = [int(p) for p in timecode.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    hours, minutes, seconds = parts
    return float(hours * 3600 + minutes * 60 + seconds)
