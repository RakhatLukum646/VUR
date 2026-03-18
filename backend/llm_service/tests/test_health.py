"""Tests for LLM service health endpoints."""

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
async def test_health_endpoint_status_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.headers["x-request-id"]


@pytest.mark.asyncio
async def test_health_endpoint_schema(client):
    data = (await client.get("/health")).json()
    assert "status" in data
    assert data["status"] in ("healthy", "degraded")
    assert data["service"] == "llm_service"
    assert "timestamp" in data
    assert "gemini_api" in data


@pytest.mark.asyncio
async def test_health_v1_endpoint_matches(client):
    """Both /health and /api/v1/health should return the same shape."""
    r1 = (await client.get("/health")).json()
    r2 = (await client.get("/api/v1/health")).json()
    assert r1["service"] == r2["service"]
    assert r1["status"] == r2["status"]


@pytest.mark.asyncio
async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.headers["x-request-id"]
    data = response.json()
    assert data["service"] == "Sign Language LLM Service"
    assert data["status"] == "running"
