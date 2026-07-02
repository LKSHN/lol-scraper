"""HUD crop-region definitions.

Broadcast overlays differ by production (LEC vs LCS vs LPL) and by the video's
resolution, so regions are expressed as fractions of the frame width/height
(0.0-1.0) rather than absolute pixels — they get scaled to the actual frame
size at OCR time.
"""

from pydantic import BaseModel


class Region(BaseModel):
    name: str
    left: float
    top: float
    right: float
    bottom: float
    # Whether OCR should grayscale/upscale/binarize this crop before reading it.
    # Verified (on the calibration frame) to fix K/decimal-point misreads on the
    # small stylized gold digits, but it distorts thin characters like ":" — so
    # it's opt-in per region rather than applied uniformly. See
    # ocr/easyocr_provider.py for the actual preprocessing.
    binarize: bool = False


# Calibrated against the official "LoL Esports" broadcast overlay (MSI 2026
# Play-Ins, T1 vs Team Liquid Alienware, youtube.com/watch?v=YoJxctwg2Yc,
# 640x360, ~10min in). Team gold is shown in "K" shorthand (e.g. "3.3K"), not
# plain digits, and the match clock sits in a separate row below the team
# scoreboard bar rather than dead-center at the very top — both differ from
# earlier placeholder assumptions. Other productions (LEC, LCS, LPL) use
# different overlays and still need their own calibration pass.
DEFAULT_REGIONS: list[Region] = [
    Region(name="game_clock", left=0.465, top=0.060, right=0.535, bottom=0.100),
    Region(
        name="blue_team_gold",
        left=0.400, top=0.005, right=0.460, bottom=0.048,
        binarize=True,
    ),
    Region(
        name="red_team_gold",
        left=0.530, top=0.005, right=0.590, bottom=0.048,
        binarize=True,
    ),
]


def scale_region(region: Region, frame_width: int, frame_height: int) -> tuple[int, int, int, int]:
    """Convert a fractional Region into absolute pixel (left, top, right, bottom)."""
    return (
        round(region.left * frame_width),
        round(region.top * frame_height),
        round(region.right * frame_width),
        round(region.bottom * frame_height),
    )
