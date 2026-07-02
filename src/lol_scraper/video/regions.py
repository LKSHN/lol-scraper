"""HUD crop-region definitions.

Broadcast overlays differ by production (LEC vs LCS vs LPL) and by the video's
resolution, so regions are expressed as fractions of the frame width/height
(0.0-1.0) rather than absolute pixels — they get scaled to the actual frame
size at OCR time. Coordinates need calibrating against a real VOD frame per
broadcast layout; the values below are rough placeholders for a 16:9 stream.
"""

from pydantic import BaseModel


class Region(BaseModel):
    name: str
    left: float
    top: float
    right: float
    bottom: float


# TODO: calibrate against a real LEC/LCS broadcast frame.
DEFAULT_REGIONS: list[Region] = [
    Region(name="game_clock", left=0.46, top=0.02, right=0.54, bottom=0.06),
    Region(name="blue_team_gold", left=0.02, top=0.02, right=0.10, bottom=0.06),
    Region(name="red_team_gold", left=0.90, top=0.02, right=0.98, bottom=0.06),
]


def scale_region(region: Region, frame_width: int, frame_height: int) -> tuple[int, int, int, int]:
    """Convert a fractional Region into absolute pixel (left, top, right, bottom)."""
    return (
        round(region.left * frame_width),
        round(region.top * frame_height),
        round(region.right * frame_width),
        round(region.bottom * frame_height),
    )
