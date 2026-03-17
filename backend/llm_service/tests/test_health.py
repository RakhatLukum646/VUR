"""Tests for LLM service health endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint_status_ok(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_schema(client):
    data = client.get("/health").json()
    assert "status" in data
    assert data["status"] in ("healthy", "degraded")
    assert data["service"] == "llm_service"
    assert "timestamp" in data
    assert "gemini_api" in data


def test_health_v1_endpoint_matches(client):
    """Both /health and /api/v1/health should return the same shape."""
    r1 = client.get("/health").json()
    r2 = client.get("/api/v1/health").json()
    assert r1["service"] == r2["service"]
    assert r1["status"] == r2["status"]


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Sign Language LLM Service"
    assert data["status"] == "running"
