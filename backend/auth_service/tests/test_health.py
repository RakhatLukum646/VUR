import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _reload_main_module():
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name)

    return importlib.import_module("app.main")


@pytest.fixture()
def auth_env(monkeypatch):
    monkeypatch.setenv("mongodb_url", "mongodb://localhost:27017")
    monkeypatch.setenv("mongodb_db", "vur_test")
    monkeypatch.setenv("jwt_secret", "test-secret-key-for-health-testing-1234567")
    monkeypatch.setenv("email_host", "smtp.example.com")
    monkeypatch.setenv("email_port", "587")
    monkeypatch.setenv("email_user", "noreply@example.com")
    monkeypatch.setenv("email_password", "password")


@pytest.fixture()
def client(auth_env, monkeypatch):
    auth_main = _reload_main_module()

    async def _noop():
        return None

    monkeypatch.setattr(auth_main, "ensure_db_ready", _noop)

    with TestClient(auth_main.create_app()) as test_client:
        yield test_client


def test_health_endpoint_reports_status_and_request_id(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "auth_service"
    assert "timestamp" in data


def test_root_endpoint_includes_request_id(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["x-request-id"]
    assert response.json()["message"] == "Auth service is running"
