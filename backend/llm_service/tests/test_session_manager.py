"""Tests for session manager."""
import pytest
from app.context.session_manager import SessionManager, Session


@pytest.fixture
def manager():
    """Create session manager fixture."""
    return SessionManager()


def test_create_session(manager):
    """Test session creation."""
    session_id = manager.create_session()
    
    assert session_id is not None
    assert len(session_id) > 0
    
    session = manager.get_session(session_id)
    assert session is not None
    assert session.session_id == session_id


def test_get_context(manager):
    """Test getting context."""
    session_id = manager.create_session()
    
    context = manager.get_context(session_id)
    assert context == ""


def test_add_interaction(manager):
    """Test adding interaction."""
    session_id = manager.create_session()
    
    success = manager.add_interaction(
        session_id,
        ["H", "I"],
        "Hi!"
    )
    
    assert success is True
    
    session = manager.get_session(session_id)
    assert session.current_context == "Hi!"
    assert len(session.history) == 1


def test_delete_session(manager):
    """Test session deletion."""
    session_id = manager.create_session()
    
    success = manager.delete_session(session_id)
    assert success is True
    
    session = manager.get_session(session_id)
    assert session is None


def test_get_nonexistent_session(manager):
    """Test getting non-existent session."""
    session = manager.get_session("invalid-id")
    assert session is None
