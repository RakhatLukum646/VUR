"""Tests for Gemini client."""
import pytest
from app.clients.gemini_client import GeminiClient


@pytest.fixture
def client():
    """Create Gemini client fixture."""
    return GeminiClient()


@pytest.mark.asyncio
async def test_fallback_translate(client):
    """Test fallback translation."""
    result = await client.translate_signs(["H", "E", "L", "L", "O"])
    
    assert "translation" in result
    assert result["fallback"] is True
    assert result["confidence"] == 0.5


@pytest.mark.asyncio
async def test_translate_hello(client):
    """Test translation of hello."""
    result = await client.translate_signs(["H", "E", "L", "L", "O"])
    
    assert "Hello" in result["translation"] or "hello" in result["translation"].lower()


@pytest.mark.asyncio
async def test_translate_thankyou(client):
    """Test translation of thank you."""
    result = await client.translate_signs(["T", "H", "A", "N", "K", "Y", "O", "U"])
    
    assert "thank" in result["translation"].lower()
