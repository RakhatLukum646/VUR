"""Configuration for LLM Service."""
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


SYSTEM_PROMPT = (
    "Ты — ИИ-сурдопереводчик. Твоя задача — получать сырой набор слов, "
    "распознанных из языка жестов, и превращать их в одно грамматически "
    "правильное, связное предложение на русском языке. Не добавляй от себя "
    "лишнего смысла. Пример: Вход: 'я хотеть пить вода' -> Выход: 'Я хочу "
    "попить воды'."
)


class Settings:
    """Application settings."""

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

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
