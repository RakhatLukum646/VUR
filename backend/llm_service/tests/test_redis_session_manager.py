"""Unit tests for RedisSessionManager using fakeredis."""
import fakeredis
import pytest

from app.context.redis_session_manager import RedisSessionManager


@pytest.fixture
def manager() -> RedisSessionManager:
    """RedisSessionManager with an in-process fakeredis backend.

    Bypasses the constructor's network connect attempt and injects a fake
    client so every public method can be exercised without a live Redis.
    """
    mgr = object.__new__(RedisSessionManager)
    mgr._ttl = 1800
    mgr._client = fakeredis.FakeRedis(decode_responses=True)
    return mgr


@pytest.fixture
def unavailable() -> RedisSessionManager:
    """RedisSessionManager with no Redis connection (simulates startup failure)."""
    mgr = object.__new__(RedisSessionManager)
    mgr._ttl = 1800
    mgr._client = None
    return mgr


# ------------------------------------------------------------------
# is_available
# ------------------------------------------------------------------

def test_is_available_when_connected(manager):
    assert manager.is_available is True


def test_is_not_available_without_client(unavailable):
    assert unavailable.is_available is False


# ------------------------------------------------------------------
# create_session / create_session_with_id
# ------------------------------------------------------------------

def test_create_session_returns_uuid(manager):
    session_id = manager.create_session()
    assert session_id
    assert len(session_id) == 36  # UUID4 format


def test_create_session_persists_data(manager):
    session_id = manager.create_session()
    data = manager.get_session(session_id)
    assert data is not None
    assert data["session_id"] == session_id
    assert data["history"] == []
    assert data["context"] == ""


def test_create_session_with_id_creates_if_absent(manager):
    sid = "my-custom-session"
    result = manager.create_session_with_id(sid)
    assert result == sid
    assert manager.get_session(sid) is not None


def test_create_session_with_id_does_not_overwrite_existing(manager):
    sid = manager.create_session()
    manager.add_interaction(sid, ["A"], "hello")
    manager.create_session_with_id(sid)  # should be a no-op
    data = manager.get_session(sid)
    assert len(data["history"]) == 1  # existing interaction preserved


# ------------------------------------------------------------------
# get_session / get_context
# ------------------------------------------------------------------

def test_get_session_returns_none_for_unknown(manager):
    assert manager.get_session("ghost") is None


def test_get_context_returns_empty_for_unknown(manager):
    assert manager.get_context("ghost") == ""


def test_get_context_returns_last_translation(manager):
    sid = manager.create_session()
    manager.add_interaction(sid, ["H", "I"], "Hello")
    assert manager.get_context(sid) == "Hello"


# ------------------------------------------------------------------
# add_interaction
# ------------------------------------------------------------------

def test_add_interaction_appends_to_history(manager):
    sid = manager.create_session()
    result = manager.add_interaction(sid, ["T", "Y"], "Thank you")
    assert result is True
    data = manager.get_session(sid)
    assert len(data["history"]) == 1
    assert data["history"][0]["signs"] == ["T", "Y"]
    assert data["history"][0]["translation"] == "Thank you"


def test_add_interaction_caps_history_at_ten(manager):
    sid = manager.create_session()
    for i in range(12):
        manager.add_interaction(sid, [str(i)], f"trans-{i}")
    data = manager.get_session(sid)
    assert len(data["history"]) == 10


def test_add_interaction_returns_false_for_unknown_session(manager):
    assert manager.add_interaction("ghost", ["A"], "hello") is False


# ------------------------------------------------------------------
# delete_session
# ------------------------------------------------------------------

def test_delete_session_removes_data(manager):
    sid = manager.create_session()
    result = manager.delete_session(sid)
    assert result is True
    assert manager.get_session(sid) is None


def test_delete_nonexistent_session_returns_false(manager):
    assert manager.delete_session("ghost") is False


# ------------------------------------------------------------------
# cleanup_expired / get_stats
# ------------------------------------------------------------------

def test_cleanup_expired_is_noop(manager):
    manager.create_session()
    assert manager.cleanup_expired() == 0


def test_get_stats_reflects_session_count(manager):
    manager.create_session()
    manager.create_session()
    stats = manager.get_stats()
    assert stats["total_sessions"] == 2
    assert stats["backend"] == "redis"


def test_get_stats_without_client(unavailable):
    stats = unavailable.get_stats()
    assert stats["total_sessions"] == 0
    assert stats["backend"] == "redis"


# ------------------------------------------------------------------
# Fallback behaviour when client is None
# ------------------------------------------------------------------

def test_load_returns_none_without_client(unavailable):
    assert unavailable._load("any") is None


def test_save_is_noop_without_client(unavailable):
    unavailable._save({"session_id": "x"})  # must not raise


def test_delete_returns_false_without_client(unavailable):
    assert unavailable._delete("any") is False
