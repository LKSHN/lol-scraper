from pathlib import Path

import numpy as np
from PIL import Image

from lol_scraper.video.regions import Region, scale_region

# Verified (calibration frames, see regions.py) to be substantially more accurate
# than EasyOCR on this broadcast's stylized HUD font -- correctly reads clock and
# gold digits (incl. the "K" glyph and decimal point that trip up EasyOCR) at
# >99% confidence with no allowlist/binarize workarounds needed. A plain
# grayscale upscale is still applied: PaddleOCR's detector needs more than the
# few dozen native pixels these crops have to find text reliably at all.
_UPSCALE = 4


class PaddleOCRProvider:
    """OCRProvider backed by PaddleOCR."""

    def __init__(self, lang: str = "en") -> None:
        from paddleocr import PaddleOCR  # deferred: heavy import, only paid on first real use

        self._ocr = PaddleOCR(
            lang=lang,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            # Works around a CPU/oneDNN crash (NotImplementedError from Paddle's
            # oneDNN backend) hit on this project's dev machine; didn't cost any
            # accuracy in testing.
            enable_mkldnn=False,
        )

    def read_regions(self, frame_path: Path, regions: list[Region]) -> dict[str, str]:
        image = Image.open(frame_path)
        width, height = image.size

        results: dict[str, str] = {}
        for region in regions:
            left, top, right, bottom = scale_region(region, width, height)
            crop = image.crop((left, top, right, bottom)).convert("L")
            size = (crop.width * _UPSCALE, crop.height * _UPSCALE)
            big = crop.resize(size, Image.Resampling.LANCZOS).convert("RGB")

            predictions = list(self._ocr.predict(np.array(big)))
            texts = predictions[0]["rec_texts"] if predictions else []
            results[region.name] = " ".join(texts).strip()
        return results
