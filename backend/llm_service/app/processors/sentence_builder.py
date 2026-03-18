"""Sentence builder for sign language translation."""
import time
import logging
from typing import List, Optional

from app.clients.gemini_client import GeminiClient
from app.config import get_settings
from app.context.session_manager import SessionManager

logger = logging.getLogger(__name__)


def _build_session_manager():
    """Return a Redis-backed or in-memory session manager based on config."""
    settings = get_settings()
    if settings.USE_REDIS:
        from app.context.redis_session_manager import RedisSessionManager
        mgr = RedisSessionManager(redis_url=settings.REDIS_URL)
        if mgr.is_available:
            logger.info("Using Redis session storage.")
            return mgr
        logger.warning("Redis unavailable — falling back to in-memory sessions.")
    return SessionManager()


class SentenceBuilder:
    """Builds natural language sentences from sign sequences."""

    def __init__(self):
        self.gemini = GeminiClient()
        self.sessions = _build_session_manager()
        logger.info("SentenceBuilder initialized")

    async def process(
        self,
        sign_sequence: List[str],
        session_id: str,
        context: Optional[str] = None,
        language: str = "ru",
    ) -> dict:
        session = self.sessions.get_session(session_id)
        if session is None:
            self.sessions.create_session_with_id(session_id)

        if context is None:
            context = self.sessions.get_context(session_id)

        start = time.monotonic()
        result = await self.gemini.translate_signs(sign_sequence, context, language)
        processing_time = int((time.monotonic() - start) * 1000)

        translation = result["translation"]
        self.sessions.add_interaction(session_id, sign_sequence, translation)

        return {
            "translation": translation,
            "confidence": result.get("confidence", 0.9),
            "session_id": session_id,
            "processing_time_ms": processing_time,
            "alternatives": result.get("alternatives", []),
            "fallback": result.get("fallback", False),
        }

    async def translate_batch(
        self,
        sign_sequences: List[List[str]],
        session_id: str,
        language: str = "ru",
    ) -> List[dict]:
        results = []
        context = ""

        for signs in sign_sequences:
            result = await self.process(signs, session_id, context, language)
            results.append(result)
            context = result["translation"]

        return results

    def create_session(self) -> str:
        return self.sessions.create_session()

    def get_session_context(self, session_id: str) -> dict:
        session = self.sessions.get_session(session_id)
        if session is None:
            return {"error": "Session not found"}
        # SessionManager returns a Session dataclass; RedisSessionManager
        # returns a plain dict — handle both.
        if hasattr(session, "to_dict"):
            return session.to_dict()
        return session

    def clear_session(self, session_id: str) -> bool:
        return self.sessions.delete_session(session_id)

    def is_healthy(self) -> bool:
        return self.gemini.is_healthy()
