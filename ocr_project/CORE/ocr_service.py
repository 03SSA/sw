from typing import List

try:
    import numpy as np
except ImportError:
    np = None

from CORE.ocr_engine import create_ocr_engine


def clean_ocr_text(lines: List[str]) -> List[str]:
    if not lines:
        return lines
    
    cleaned = []
    for line in lines:
        if not line:
            continue
        line = line.strip()
        if line:
            cleaned.append(line)
    
    while cleaned and not cleaned[-1]:
        cleaned.pop()
    
    return cleaned


class OCRService:
    def __init__(self) -> None:
        self.languages = ["ko", "en"]
        self.engine = create_ocr_engine(self.languages)

    def set_languages(self, languages: List[str]) -> None:
        normalized = []
        for lang in languages:
            if lang and lang not in normalized:
                normalized.append(lang)

        if not normalized:
            normalized = ["ko", "en"]

        if normalized == self.languages and self.engine is not None:
            return

        self.languages = normalized
        self.engine = create_ocr_engine(self.languages)

    def is_available(self) -> bool:
        return self.engine is not None and np is not None and self.engine.is_available()

    def recognize_image(self, image) -> List[str]:
        if self.engine is None:
            raise RuntimeError("OCR engine is not available.")
        if np is None:
            raise RuntimeError("numpy is not installed.")
        if not self.engine.is_available():
            raise RuntimeError("OCR engine failed to initialize for the selected language pair.")

        image_array = np.array(image)
        result = self.engine.read_text_simple(image_array)
        return clean_ocr_text([line for line in result if line])
