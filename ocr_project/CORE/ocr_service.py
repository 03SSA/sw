from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import quote
from urllib.request import Request, urlopen
import json
import re

try:
    import numpy as np
except ImportError:
    np = None

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
except ImportError:
    Image = None
    ImageEnhance = None
    ImageFilter = None
    ImageOps = None

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

from CORE.ocr_engine import create_ocr_engine


@dataclass
class OCRTranslationResult:
    original_lines: List[str]
    original_text: str
    translated_text: str
    source_language: str
    target_language: str


class OCRService:
    def __init__(self) -> None:
        self.languages = ["ko", "en"]
        self.engine = create_ocr_engine(self.languages)
        self.preprocessing_enabled = True
        self.upscale_factor = 2
        self.contrast_factor = 1.6
        self.sharpness_factor = 1.4

    def recognize_image_raw(self, image) -> List[str]:
        if self.engine is None:
            raise RuntimeError("OCR engine is not available.")
        if np is None:
            raise RuntimeError("numpy is not installed.")

        image_array = np.array(image)
        result = self.engine.read_text_simple(image_array)
        return [line.strip() for line in result if line and line.strip()]

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

        prepared_image = self.preprocess_image(image)
        image_array = np.array(prepared_image)
        result = self.engine.read_text_simple(image_array)
        return [line.strip() for line in result if line and line.strip()]

    def set_preprocessing(
        self,
        enabled: bool = True,
        upscale_factor: int = 2,
        contrast_factor: float = 1.6,
        sharpness_factor: float = 1.4,
    ) -> None:
        self.preprocessing_enabled = enabled
        self.upscale_factor = max(1, int(upscale_factor))
        self.contrast_factor = max(0.1, float(contrast_factor))
        self.sharpness_factor = max(0.1, float(sharpness_factor))

    def preprocess_image(self, image):
        if not self.preprocessing_enabled:
            return image

        if Image is None or ImageOps is None or ImageEnhance is None or ImageFilter is None:
            return image

        try:
            prepared = image

            if not isinstance(prepared, Image.Image):
                prepared = Image.fromarray(np.array(prepared))

            prepared = prepared.convert("L")

            if self.upscale_factor > 1:
                width, height = prepared.size
                prepared = prepared.resize(
                    (width * self.upscale_factor, height * self.upscale_factor),
                    Image.Resampling.LANCZOS,
                )

            prepared = ImageOps.autocontrast(prepared)
            prepared = ImageEnhance.Contrast(prepared).enhance(self.contrast_factor)
            prepared = ImageEnhance.Sharpness(prepared).enhance(self.sharpness_factor)
            prepared = prepared.filter(
                ImageFilter.UnsharpMask(radius=1, percent=130, threshold=3)
            )

            return prepared
        except Exception:
            return image

    def recognize_and_translate(
        self,
        image,
        source_language: str = "auto",
        target_language: str = "ko",
    ) -> OCRTranslationResult:
        lines = self.recognize_image(image)
        original_text = self.join_lines(lines)
        translated_text = self.translate_text(
            original_text,
            source_language=source_language,
            target_language=target_language,
        )

        return OCRTranslationResult(
            original_lines=lines,
            original_text=original_text,
            translated_text=translated_text,
            source_language=source_language,
            target_language=target_language,
        )

    def translate_lines(
        self,
        lines: List[str],
        source_language: str = "auto",
        target_language: str = "ko",
    ) -> str:
        clean_lines = self.clean_ocr_lines(lines)

        if not clean_lines:
            return ""

        return self.translate_text(
            self.join_lines_for_translation(clean_lines),
            source_language=source_language,
            target_language=target_language,
        )

    def translate_text(
        self,
        text: str,
        source_language: str = "auto",
        target_language: str = "ko",
    ) -> str:
        clean_text = self.clean_text_for_translation(text)

        if not clean_text:
            return ""

        normalized_source = self._normalize_translation_language(
            source_language,
            default="auto",
        )
        normalized_target = self._normalize_translation_language(
            target_language,
            default="ko",
        )

        chunks = self._split_translation_chunks(clean_text)
        translated_chunks = []

        for chunk in chunks:
            translated = self._translate_chunk(
                chunk,
                source_language=normalized_source,
                target_language=normalized_target,
            )

            if translated:
                translated_chunks.append(translated)

        if translated_chunks:
            return "\n".join(translated_chunks).strip()

        raise RuntimeError(
            "Translation is not available. Install deep-translator with "
            "`pip install deep-translator`, check the internet connection, then try again."
        )

    def join_lines(self, lines: List[str]) -> str:
        return "\n".join(line.strip() for line in lines if line and line.strip())

    def clean_ocr_lines(self, lines: List[str]) -> List[str]:
        cleaned = []

        for line in lines:
            text = self.clean_text_for_translation(line)
            if text:
                cleaned.append(text)

        return cleaned

    def clean_text_for_translation(self, text: str) -> str:
        value = (text or "").strip()

        if not value:
            return ""

        value = value.replace("\r\n", "\n").replace("\r", "\n")
        value = re.sub(r"[ \t]+", " ", value)
        value = re.sub(r" ?-\n ?", "", value)
        value = re.sub(r"\n{3,}", "\n\n", value)

        return value.strip()

    def join_lines_for_translation(self, lines: List[str]) -> str:
        if not lines:
            return ""

        joined = " ".join(line.strip() for line in lines if line and line.strip())
        joined = re.sub(r"\s+([,.!?;:%])", r"\1", joined)
        joined = re.sub(r"([.!?])\s+", r"\1\n", joined)

        return joined.strip()

    def _split_translation_chunks(self, text: str, max_length: int = 1500) -> List[str]:
        paragraphs = [part.strip() for part in re.split(r"\n+", text) if part.strip()]
        chunks = []
        current = ""

        for paragraph in paragraphs:
            if len(paragraph) > max_length:
                if current:
                    chunks.append(current.strip())
                    current = ""

                chunks.extend(self._split_long_text(paragraph, max_length=max_length))
                continue

            candidate = f"{current}\n{paragraph}".strip() if current else paragraph

            if len(candidate) <= max_length:
                current = candidate
            else:
                chunks.append(current.strip())
                current = paragraph

        if current:
            chunks.append(current.strip())

        return chunks

    def _split_long_text(self, text: str, max_length: int) -> List[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks = []
        current = ""

        for sentence in sentences:
            if len(sentence) > max_length:
                if current:
                    chunks.append(current.strip())
                    current = ""

                chunks.extend(
                    sentence[i : i + max_length]
                    for i in range(0, len(sentence), max_length)
                )
                continue

            candidate = f"{current} {sentence}".strip() if current else sentence

            if len(candidate) <= max_length:
                current = candidate
            else:
                chunks.append(current.strip())
                current = sentence

        if current:
            chunks.append(current.strip())

        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def _translate_chunk(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> Optional[str]:
        if GoogleTranslator is not None:
            try:
                translated = GoogleTranslator(
                    source=source_language,
                    target=target_language,
                ).translate(text)

                if translated:
                    return translated.strip()
            except Exception:
                pass

        return self._translate_with_google_web(
            text,
            source_language=source_language,
            target_language=target_language,
        )

    def _normalize_translation_language(self, language: Optional[str], default: str) -> str:
        value = (language or default).strip().lower()

        aliases = {
            "ch_sim": "zh-CN",
            "ch_tra": "zh-TW",
            "zh_cn": "zh-CN",
            "zh_tw": "zh-TW",
        }

        return aliases.get(value, value)

    def _translate_with_google_web(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> Optional[str]:
        url = (
            "https://translate.googleapis.com/translate_a/single"
            "?client=gtx"
            f"&sl={quote(source_language)}"
            f"&tl={quote(target_language)}"
            "&dt=t"
            f"&q={quote(text)}"
        )

        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
            },
        )

        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

        try:
            translated_parts = [part[0] for part in payload[0] if part and part[0]]
        except Exception:
            return None

        return "".join(translated_parts).strip() or None