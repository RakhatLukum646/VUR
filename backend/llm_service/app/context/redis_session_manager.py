"""Redis-backed session storage for the LLM service.

Provides the same interface as SessionManager but persists sessions in
Redis so they survive service restarts and are shared across multiple
replicas.  Falls back gracefully to a no-op if the Redis connection
cannot be established (e.g. during local development without Redis).
"""
import json
import logging
import uuid
from datetime import datetime
from typing import List, Optional

import redis

logger = logging.getLogger(__name__)

_KEY_PREFIX = "vur:session:"


def _key(session_id: str) -> str:
    return f"{_KEY_PREFIX}{session_id}"


class RedisSessionManager:
    """SessionManager backed by Redis.

    The session data is stored as a JSON blob with a TTL equal to the
    session timeout.  The interface mirrors SessionManager exactly so
    SentenceBuilder requires no changes.
    """

    def __init__(self, redis_url: str, timeout_minutes: int = 30):
        self._ttl = timeout_minutes * 60
        self._client: Optional[redis.Redis] = None
        try:
            self._client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
            self._client.ping()
            logger.info("RedisSessionManager connected to %s", redis_url)
        except Exception as exc:
            logger.warning(
                "Redis unavailable (%s) — sessions will not be persisted.", exc
            )
            self._client = None

    @property
    def is_available(self) -> bool:
        return self._client is not None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self, session_id: str) -> Optional[dict]:
        if not self._client:
            return None
        try:
            raw = self._client.get(_key(session_id))
            return json.loads(raw) if raw else None
        except Exception as exc:
            logger.error("Redis GET error: %s", exc)
            return None

    def _save(self, data: dict) -> None:
        if not self._client:
            return
        try:
            self._client.setex(_key(data["session_id"]), self._ttl, json.dumps(data))
        except Exception as exc:
            logger.error("Redis SET error: %s", exc)

    def _delete(self, session_id: str) -> bool:
        if not self._client:
            return False
        try:
            return bool(self._client.delete(_key(session_id)))
        except Exception as exc:
            logger.error("Redis DEL error: %s", exc)
            return False

    @staticmethod
    def _new_session(session_id: str) -> dict:
        now = datetime.utcnow().isoformat()
        return {
            "session_id": session_id,
            "created_at": now,
            "last_activity": now,
            "context": "",
            "history": [],
        }

    # ------------------------------------------------------------------
    # Public interface (mirrors SessionManager)
    # ------------------------------------------------------------------

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._save(self._new_session(session_id))
        logger.info("Created Redis session: %s", session_id)
        return session_id

    def create_session_with_id(self, session_id: str) -> str:
        if not self._load(session_id):
            self._save(self._new_session(session_id))
            logger.info("Created Redis session: %s", session_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        """Return the session dict or None if not found."""
        return self._load(session_id)

    def get_context(self, session_id: str) -> str:
        data = self._load(session_id)
        return data["context"] if data else ""

    def add_interaction(self, session_id: str, signs: List[str], translation: str) -> bool:
        data = self._load(session_id)
        if not data:
            logger.warning("Session not found: %s", session_id)
            return False

        data["history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "signs": signs,
            "translation": translation,
        })
        # Keep last 10 interactions
        data["history"] = data["history"][-10:]
        data["context"] = translation
        data["last_activity"] = datetime.utcnow().isoformat()
        self._save(data)
        return True

    def delete_session(self, session_id: str) -> bool:
        deleted = self._delete(session_id)
        if deleted:
            logger.info("Deleted Redis session: %s", session_id)
        return deleted

    def cleanup_expired(self) -> int:
        # Redis handles TTL-based expiry automatically; nothing to do.
        return 0

    def get_stats(self) -> dict:
        count = 0
        if self._client:
            try:
                count = len(self._client.keys(f"{_KEY_PREFIX}*"))
            except Exception:
                pass
        return {"total_sessions": count, "backend": "redis"}
