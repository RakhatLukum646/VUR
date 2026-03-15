"""Tests for sentence builder."""
import pytest
from app.processors.sentence_builder import SentenceBuilder


@pytest.fixture
def builder():
    """Create sentence builder fixture."""
    return SentenceBuilder()


@pytest.mark.asyncio
async def test_process_signs(builder):
    """Test processing signs."""
    session_id = builder.create_session()
    
    result = await builder.process(
        sign_sequence=["H", "E", "L", "L", "O"],
        session_id=session_id
    )
    
    assert "translation" in result
    assert result["session_id"] == session_id
    assert "processing_time_ms" in result
    assert result["confidence"] > 0


@pytest.mark.asyncio
async def test_context_tracking(builder):
    """Test context is tracked across interactions."""
    session_id = builder.create_session()
    
    # First interaction
    await builder.process(
        sign_sequence=["H", "E", "L", "L", "O"],
        session_id=session_id
    )
    
    # Check context was saved
    context = builder.get_session_context(session_id)
    assert "history" in context
    assert len(context["history"]) == 1


def test_create_session(builder):
    """Test session creation."""
    session_id = builder.create_session()
    
    assert session_id is not None
    assert len(session_id) > 0


def test_clear_session(builder):
    """Test clearing session."""
    session_id = builder.create_session()
    
    success = builder.clear_session(session_id)
    assert success is True
