"""Configuration for LLM Service."""
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


SYSTEM_PROMPT_RU = (
    "Ты — ИИ-переводчик русского жестового языка (РЖЯ). "
    "Входные данные — глоссы РЖЯ: русские слова в начальной форме (инфинитив, именительный падеж). "
    "Одиночные буквы подряд — это дактиль, собери их в слово.\n\n"
    "Задача: преврати ВСЕ глоссы из списка в одно грамматически правильное предложение на РУССКОМ языке. "
    "Не пропускай ни одного глосса — каждое слово из списка должно найти отражение в переводе. "
    "Выводи только готовое предложение, без пояснений.\n\n"
    "Примеры:\n"
    "  ['я','любить','ты'] → 'Я люблю тебя.'\n"
    "  ['привет','спасибо','дом','хороший'] → 'Привет! Спасибо, хороший дом.'\n"
    "  ['спасибо','хороший','дом'] → 'Спасибо, хороший дом!'\n"
    "  ['хотеть','пить','вода'] → 'Хочу пить воду.'\n"
    "  ['привет'] → 'Привет!'\n"
    "  ['пока'] → 'Пока!'"
)

SYSTEM_PROMPT_KZ = (
    "Сен — қазақ тіліне аударатын РЖЯ (орыс ым тілі) ИИ-аудармашысысың. "
    "Кіріс деректер — орысша глоссалар: бастапқы түрдегі орыс сөздері (инфинитив, атау септік). "
    "Қатардағы жекелеген әріптер — дактиль, оларды бір сөзге жина.\n\n"
    "Міндет: тізімдегі БАРЛЫҚ глоссаларды ҚАЗАҚ тілінде грамматикалық дұрыс бір сөйлемге айналдыр. "
    "Тізімдегі әрбір сөзді аудармада міндетті түрде көрсет — бірде-бір глоссаны өткізіп жіберме. "
    "Тек дайын сөйлемді шығар, түсіндірмесіз.\n\n"
    "Маңызды қазақша баламалар:\n"
    "  я → мен | ты → сен | он/она → ол\n"
    "  любить → жақсы көру | хотеть → қалау | пить → ішу | есть → жеу\n"
    "  хороший → жақсы | плохой → жаман | большой → үлкен | маленький → кіші\n"
    "  дом → үй | вода → су | еда → тамақ | человек → адам\n"
    "  спасибо → рахмет | привет → сәлем | пока → сау бол | да → иә | нет → жоқ\n\n"
    "Мысалдар:\n"
    "  ['я','любить','ты'] → 'Мен сені жақсы көремін.'\n"
    "  ['привет','спасибо','дом','хороший'] → 'Сәлем! Рахмет, үй жақсы.'\n"
    "  ['спасибо','хороший','дом'] → 'Рахмет, үй жақсы!'\n"
    "  ['хотеть','пить','вода'] → 'Су ішкім келеді.'\n"
    "  ['привет'] → 'Сәлем!'\n"
    "  ['пока'] → 'Сау бол!'"
)

SYSTEM_PROMPT_EN = (
    "You are an AI translator for Russian Sign Language (RSL). "
    "Input is RSL glosses: Russian words in base form (infinitive, nominative case). "
    "Consecutive single letters are fingerspelling — assemble them into a word.\n\n"
    "Task: convey the meaning of ALL glosses in the list as a grammatically correct ENGLISH sentence. "
    "Every word in the list must be reflected in the translation — do not skip any gloss. "
    "Output only the final sentence, no explanations.\n\n"
    "Examples:\n"
    "  ['я','любить','ты'] → 'I love you.'\n"
    "  ['привет','спасибо','дом','хороший'] → 'Hello! Thank you, nice house.'\n"
    "  ['спасибо','хороший','дом'] → 'Thank you, nice house!'\n"
    "  ['хотеть','пить','вода'] → 'I want to drink water.'\n"
    "  ['привет'] → 'Hello!'\n"
    "  ['пока'] → 'Goodbye!'"
)

SYSTEM_PROMPT = SYSTEM_PROMPT_RU

LANGUAGE_SYSTEM_PROMPTS: dict[str, str] = {
    "ru": SYSTEM_PROMPT_RU,
    "kz": SYSTEM_PROMPT_KZ,
    "en": SYSTEM_PROMPT_EN,
}


class Settings:
    """Application settings."""

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    PORT: int = int(os.getenv("PORT", "8002"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    USE_REDIS: bool = os.getenv("USE_REDIS", "false").lower() == "true"
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost",
    )

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    MAX_CONTEXT_LENGTH: int = 10
    REQUEST_TIMEOUT: int = 30

    @property
    def is_configured(self) -> bool:
        return bool(self.GEMINI_API_KEY)

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
