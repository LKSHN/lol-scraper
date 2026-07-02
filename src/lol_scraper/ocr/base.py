from pathlib import Path
from typing import Protocol

from lol_scraper.video.regions import Region


class OCRProvider(Protocol):
    """Reads text out of named crop regions of a single frame image."""

    def read_regions(self, frame_path: Path, regions: list[Region]) -> dict[str, str]:
        """Return {region.name: raw_text} for each region, cropped from the frame."""
        ...
