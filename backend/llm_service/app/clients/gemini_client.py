"""Google Gemini API client for sign language translation."""
import logging
from typing import List, Optional

import google.generativeai as genai

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
            genai.configure(api_key=self.settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel(
                model_name=self.settings.GEMINI_MODEL,
                system_instruction=SYSTEM_PROMPT,
            )
            logger.info(f"Gemini client initialized with model: {self.settings.GEMINI_MODEL}")
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
            response = await self._model.generate_content_async(prompt)
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
        signs_text = " ".join(sign_sequence)

        lang_names = {"en": "English", "ru": "Russian", "kz": "Kazakh"}
        lang_name = lang_names.get(language, "Russian")

        prompt = f"Сырые глоссы из жестового языка: {signs_text}\n"
        if context:
            prompt += f"Предыдущий контекст: {context}\n"
        prompt += f"\nПереведи в грамматически правильное предложение на {lang_name}."
        return prompt

    def _fallback_translate(
        self,
        sign_sequence: List[str],
        context: Optional[str] = None,
    ) -> dict:
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
