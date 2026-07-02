from lol_scraper.ocr.base import OCRProvider


def get_ocr_provider(name: str) -> OCRProvider:
    if name == "paddleocr":
        from lol_scraper.ocr.paddleocr_provider import PaddleOCRProvider

        return PaddleOCRProvider()
    if name == "easyocr":
        from lol_scraper.ocr.easyocr_provider import EasyOCRProvider

        return EasyOCRProvider()
    raise ValueError(f"Unknown OCR provider {name!r} (expected 'paddleocr' or 'easyocr')")
