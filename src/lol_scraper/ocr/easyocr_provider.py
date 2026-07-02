from pathlib import Path

import numpy as np
from PIL import Image

from lol_scraper.video.regions import Region, scale_region

# Upscale factor + brightness cutoff for Region.binarize=True crops. Verified
# against the calibration frame (see regions.py) to fix EasyOCR misreading the
# stylized "K" glyph / dropping the decimal point on small gold digits.
_BINARIZE_UPSCALE = 8
_BINARIZE_THRESHOLD = 150


def _preprocess(crop: Image.Image, *, binarize: bool) -> np.ndarray:
    if not binarize:
        return np.array(crop)
    gray = crop.convert("L")
    size = (gray.width * _BINARIZE_UPSCALE, gray.height * _BINARIZE_UPSCALE)
    big = gray.resize(size, Image.LANCZOS)
    thresholded = big.point(lambda p: 255 if p > _BINARIZE_THRESHOLD else 0)
    return np.array(thresholded)


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
            array = _preprocess(crop, binarize=region.binarize)
            texts = self._reader.readtext(array, detail=0)
            results[region.name] = " ".join(texts).strip()
        return results
