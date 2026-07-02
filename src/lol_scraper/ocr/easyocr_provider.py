from pathlib import Path

import numpy as np
from PIL import Image

from lol_scraper.video.regions import Region, scale_region


class EasyOCRProvider:
    """Default OCRProvider, backed by EasyOCR (CPU by default; set gpu=True if CUDA is set up)."""

    def __init__(self, languages: list[str] | None = None, gpu: bool = False) -> None:
        import easyocr  # deferred: heavy import (torch), only paid on first real use

        self._reader = easyocr.Reader(languages or ["en"], gpu=gpu)

    def read_regions(self, frame_path: Path, regions: list[Region]) -> dict[str, str]:
        image = Image.open(frame_path)
        width, height = image.size

        results: dict[str, str] = {}
        for region in regions:
            left, top, right, bottom = scale_region(region, width, height)
            crop = image.crop((left, top, right, bottom))
            texts = self._reader.readtext(np.array(crop), detail=0)
            results[region.name] = " ".join(texts).strip()
        return results
