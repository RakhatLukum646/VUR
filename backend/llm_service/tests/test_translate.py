"""HTTP-level tests for the /api/v1/translate and session endpoints."""
import pytest
import pytest_asyncio
import httpx

from app.main import app


@pytest_asyncio.fixture
async def client():
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as c:
            yield c


@pytest.mark.asyncio
async def test_translate_auto_creates_session(client):
    """POST /translate without a session_id should auto-create one and return a translation."""
    response = await client.post(
        "/api/v1/translate",
        json={"sign_sequence": ["H", "E", "L", "L", "O"], "language": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "translation" in data
    assert "session_id" in data
    assert data["session_id"]
    assert "processing_time_ms" in data
    assert "confidence" in data


@pytest.mark.asyncio
async def test_translate_with_provided_session(client):
    """POST /translate with an explicit session_id uses the existing session."""
    create_resp = await client.post("/api/v1/sessions")
    assert create_resp.status_code == 200
    session_id = create_resp.json()["session_id"]

    translate_resp = await client.post(
        "/api/v1/translate",
        json={"sign_sequence": ["T", "H", "A", "N", "K", "S"], "session_id": session_id, "language": "en"},
    )
    assert translate_resp.status_code == 200
    assert translate_resp.json()["session_id"] == session_id


@pytest.mark.asyncio
async def test_create_session_endpoint(client):
    """POST /sessions creates a new session and returns its id."""
    response = await client.post("/api/v1/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["session_id"]
    assert "message" in data


@pytest.mark.asyncio
async def test_get_context_returns_session_data(client):
    """GET /context/{id} returns session history after a translation."""
    create_resp = await client.post("/api/v1/sessions")
    session_id = create_resp.json()["session_id"]

    await client.post(
        "/api/v1/translate",
        json={"sign_sequence": ["H", "I"], "session_id": session_id, "language": "en"},
    )

    ctx_resp = await client.get(f"/api/v1/context/{session_id}")
    assert ctx_resp.status_code == 200
    data = ctx_resp.json()
    assert data["session_id"] == session_id
    assert "history" in data
    assert len(data["history"]) >= 1


@pytest.mark.asyncio
async def test_get_context_not_found(client):
    """GET /context/{id} returns 404 for an unknown session_id."""
    response = await client.get("/api/v1/context/nonexistent-session-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_clear_session_success(client):
    """DELETE /context/{id} removes the session and returns 200."""
    create_resp = await client.post("/api/v1/sessions")
    session_id = create_resp.json()["session_id"]

    delete_resp = await client.delete(f"/api/v1/context/{session_id}")
    assert delete_resp.status_code == 200
    data = delete_resp.json()
    assert data["session_id"] == session_id


@pytest.mark.asyncio
async def test_clear_session_not_found(client):
    """DELETE /context/{id} returns 404 for an unknown session_id."""
    response = await client.delete("/api/v1/context/nonexistent-session-id")
    assert response.status_code == 404
