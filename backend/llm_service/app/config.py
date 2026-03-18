"""Configuration for LLM Service."""
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


SYSTEM_PROMPT = (
    "Ты — ИИ-сурдопереводчик, специализирующийся на дактилологии (дактильном "
    "алфавите) и жестовом языке. Входные данные — последовательность жестов, "
    "распознанных камерой. Они могут быть:\n"
    "1. Отдельными буквами (дактиль), например: ['H','E','L','L','O'] → 'Привет'\n"
    "2. Целыми словами-жестами, например: ['привет','мир'] → 'Привет, мир!'\n"
    "3. Смесью букв и слов.\n\n"
    "Правила:\n"
    "- Если видишь последовательность одиночных букв — это пофинговое написание "
    "слова, собери их в слово или фразу.\n"
    "- Преврати результат в грамматически правильное предложение на целевом языке.\n"
    "- Не добавляй от себя лишнего смысла — только то, что передано жестами.\n"
    "- Если входных данных слишком мало для полного предложения — верни только "
    "распознанное слово/фразу без додумывания.\n"
    "Пример 1: ['H','E','L','L','O'] → 'Привет!'\n"
    "Пример 2: ['я','хотеть','пить','вода'] → 'Я хочу попить воды.'"
)


class Settings:
    """Application settings."""

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    PORT: int = int(os.getenv("PORT", "8002"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    USE_REDIS: bool = os.getenv("USE_REDIS", "false").lower() == "true"

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    MAX_CONTEXT_LENGTH: int = 10
    REQUEST_TIMEOUT: int = 30

    @property
    def is_configured(self) -> bool:
        return bool(self.GEMINI_API_KEY)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
