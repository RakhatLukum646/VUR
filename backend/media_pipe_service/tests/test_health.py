"""Tests for MediaPipe service health endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint_status_ok(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_endpoint_schema(client):
    data = client.get("/api/v1/health").json()
    assert data["status"] == "healthy"
    assert data["service"] == "media_pipe"
    assert "timestamp" in data
    assert "version" in data


def test_readiness_endpoint_status_ok(client):
    response = client.get("/api/v1/ready")
    assert response.status_code == 200


def test_readiness_endpoint_schema(client):
    data = client.get("/api/v1/ready").json()
    assert data["ready"] is True
    assert data["service"] == "media_pipe"
