"""Google Gemini API client for sign language translation."""
import logging
from typing import List, Optional

from google import genai
from google.genai import types

from app.config import get_settings, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class GeminiClient:
    """Async client for the Google Gemini API."""

    def __init__(self):
        self.settings = get_settings()
        self._model = None
        self._initialize()

    def _initialize(self):
        if not self.settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set. LLM features will be unavailable.")
            return

        try:
            self._model = genai.Client(api_key=self.settings.GEMINI_API_KEY)
            logger.info(
                "Gemini client initialized with model: %s",
                self.settings.GEMINI_MODEL,
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise

    async def translate_signs(
        self,
        sign_sequence: List[str],
        context: Optional[str] = None,
        language: str = "ru",
    ) -> dict:
        """Translate sign sequence to natural language using Gemini."""
        if not self._model:
            return self._fallback_translate(sign_sequence, context)

        prompt = self._build_prompt(sign_sequence, context, language)

        try:
            response = await self._model.aio.models.generate_content(
                model=self.settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.2,
                    max_output_tokens=128,
                ),
            )
            translation = response.text.strip()

            return {
                "translation": translation,
                "confidence": 0.92,
                "alternatives": [],
                "raw_signs": " ".join(sign_sequence),
            }
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._fallback_translate(sign_sequence, context)

    def _build_prompt(
        self,
        sign_sequence: List[str],
        context: Optional[str],
        language: str,
    ) -> str:
        lang_names = {"en": "English", "ru": "Russian", "kz": "Kazakh"}
        lang_name = lang_names.get(language, "Russian")

        # Detect whether the sequence looks like fingerspelling (single chars)
        # or whole-word glosses, and hint the model accordingly.
        all_single_chars = all(len(s) == 1 for s in sign_sequence)
        if all_single_chars:
            signs_repr = "".join(sign_sequence)
            input_type_hint = (
                f"Дактильная последовательность (буква за буквой): '{signs_repr}' "
                f"(каждый символ — отдельный жест)"
            )
        else:
            signs_repr = " | ".join(sign_sequence)
            input_type_hint = f"Жестовые глоссы: {signs_repr}"

        prompt = f"{input_type_hint}\n"
        if context:
            prompt += f"Предыдущий контекст разговора: {context}\n"
        prompt += (
            f"\nПреобразуй это в грамматически правильное предложение на {lang_name}. "
            "Выведи только готовое предложение, без пояснений."
        )
        return prompt

    def _fallback_translate(
        self,
        sign_sequence: List[str],
        context: Optional[str] = None,
    ) -> dict:
        if all(len(s) == 1 for s in sign_sequence):
            text = "".join(sign_sequence).lower()
        else:
            text = " ".join(sign_sequence).lower()

        common = {
            "привет": "Привет!",
            "hello": "Hello!",
            "спасибо": "Спасибо!",
            "пока": "Пока!",
        }
        translation = common.get(text, text.capitalize())

        return {
            "translation": translation,
            "confidence": 0.5,
            "alternatives": [],
            "raw_signs": text,
            "fallback": True,
        }

    def is_healthy(self) -> bool:
        return self._model is not None
