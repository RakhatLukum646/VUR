import importlib
import sys
from pathlib import Path

import mongomock
import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class _AsyncCollection:
    def __init__(self, col):
        self._col = col

    async def find_one(self, query=None, *args, **kwargs):
        return self._col.find_one(query or {}, *args, **kwargs)

    async def insert_one(self, document):
        return self._col.insert_one(document)

    async def update_one(self, query, update, **kwargs):
        return self._col.update_one(query, update, **kwargs)

    async def update_many(self, query, update, **kwargs):
        return self._col.update_many(query, update, **kwargs)

    async def delete_many(self, query):
        return self._col.delete_many(query)

    async def create_index(self, *args, **kwargs):
        return self._col.create_index(*args, **kwargs)

    def insert_seed(self, **document) -> dict:
        doc = dict(document)
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        self._col.insert_one(doc)
        return doc


@pytest.fixture()
def csrf_client(monkeypatch):
    monkeypatch.setenv("mongodb_url", "mongodb://localhost:27017")
    monkeypatch.setenv("mongodb_db", "vur_test")
    monkeypatch.setenv("jwt_secret", "test-secret-key-for-csrf-testing-1234567")
    monkeypatch.setenv("email_host", "smtp.example.com")
    monkeypatch.setenv("email_port", "587")
    monkeypatch.setenv("email_user", "noreply@example.com")
    monkeypatch.setenv("email_password", "password")
    monkeypatch.setenv("frontend_url", "http://localhost:5173")

    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name)

    auth_main = importlib.import_module("app.main")
    auth_router = importlib.import_module("app.routers.auth")
    auth_db = importlib.import_module("app.db")
    auth_dependencies = importlib.import_module("app.dependencies")
    auth_rate_limit = importlib.import_module("app.rate_limit")
    password_reset_service = importlib.import_module("app.services.password_reset_service")
    session_service = importlib.import_module("app.services.session_service")

    mm_db = mongomock.MongoClient()["vur_test"]
    fake_users = _AsyncCollection(mm_db["users"])
    fake_sessions = _AsyncCollection(mm_db["auth_sessions"])
    fake_resets = _AsyncCollection(mm_db["password_reset_tokens"])

    monkeypatch.setattr(auth_db, "users_collection", fake_users)
    monkeypatch.setattr(auth_db, "auth_sessions_collection", fake_sessions)
    monkeypatch.setattr(auth_db, "password_reset_tokens_collection", fake_resets)
    monkeypatch.setattr(auth_router, "users_collection", fake_users)
    monkeypatch.setattr(auth_router, "password_reset_tokens_collection", fake_resets)
    monkeypatch.setattr(auth_dependencies, "users_collection", fake_users)
    monkeypatch.setattr(session_service, "auth_sessions_collection", fake_sessions)
    monkeypatch.setattr(password_reset_service, "password_reset_tokens_collection", fake_resets)
    monkeypatch.setattr(auth_router, "send_verification_email", lambda *a: None)
    monkeypatch.setattr(auth_router, "send_password_reset_email", lambda *a: None)

    async def _noop():
        return None

    monkeypatch.setattr(auth_main, "ensure_db_ready", _noop)
    auth_rate_limit.limiter._hits.clear()

    with TestClient(auth_main.create_app()) as c:
        yield c


# ── GET /auth/csrf-token ──────────────────────────────────────────────────


def test_csrf_token_endpoint_returns_token(csrf_client):
    response = csrf_client.get("/auth/csrf-token")
    assert response.status_code == 200
    data = response.json()
    assert "csrf_token" in data
    assert len(data["csrf_token"]) >= 32


def test_csrf_token_sets_non_httponly_cookie(csrf_client):
    response = csrf_client.get("/auth/csrf-token")
    assert response.status_code == 200
    assert "vur_csrf_token" in response.cookies
    set_cookie = response.headers.get("set-cookie", "")
    assert "httponly" not in set_cookie.lower(), (
        "vur_csrf_token must NOT be HttpOnly so JavaScript can read it"
    )


def test_csrf_token_changes_on_each_request(csrf_client):
    r1 = csrf_client.get("/auth/csrf-token")
    r2 = csrf_client.get("/auth/csrf-token")
    assert r1.json()["csrf_token"] != r2.json()["csrf_token"]


# ── POST /auth/register ───────────────────────────────────────────────────


def test_register_without_csrf_header_returns_403(csrf_client):
    csrf_client.get("/auth/csrf-token")  # sets cookie but we don't pass header
    response = csrf_client.post(
        "/auth/register",
        json={"name": "Alice", "email": "a@example.com", "password": "supersecret"},
    )
    assert response.status_code == 403


def test_register_without_csrf_cookie_returns_403(csrf_client):
    response = csrf_client.post(
        "/auth/register",
        json={"name": "Alice", "email": "a@example.com", "password": "supersecret"},
        headers={"X-CSRF-Token": "some-token"},
    )
    assert response.status_code == 403


def test_register_with_wrong_csrf_header_returns_403(csrf_client):
    csrf_client.get("/auth/csrf-token")
    response = csrf_client.post(
        "/auth/register",
        json={"name": "Alice", "email": "a@example.com", "password": "supersecret"},
        headers={"X-CSRF-Token": "completely-wrong-token"},
    )
    assert response.status_code == 403


def test_register_with_valid_csrf_token_succeeds(csrf_client):
    r = csrf_client.get("/auth/csrf-token")
    token = r.json()["csrf_token"]

    response = csrf_client.post(
        "/auth/register",
        json={"name": "Alice", "email": "a@example.com", "password": "supersecret"},
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 200


# ── POST /auth/login ──────────────────────────────────────────────────────


def test_login_without_csrf_header_returns_403(csrf_client):
    csrf_client.get("/auth/csrf-token")
    response = csrf_client.post(
        "/auth/login",
        json={"email": "a@example.com", "password": "supersecret"},
    )
    assert response.status_code == 403


# ── POST /auth/logout ─────────────────────────────────────────────────────


def test_logout_without_csrf_header_returns_403(csrf_client):
    csrf_client.get("/auth/csrf-token")
    response = csrf_client.post("/auth/logout")
    assert response.status_code == 403


# ── POST /auth/password-reset/request ────────────────────────────────────


def test_password_reset_request_without_csrf_returns_403(csrf_client):
    csrf_client.get("/auth/csrf-token")
    response = csrf_client.post(
        "/auth/password-reset/request",
        json={"email": "a@example.com"},
    )
    assert response.status_code == 403


def test_password_reset_request_with_csrf_succeeds(csrf_client):
    r = csrf_client.get("/auth/csrf-token")
    token = r.json()["csrf_token"]
    response = csrf_client.post(
        "/auth/password-reset/request",
        json={"email": "nonexistent@example.com"},
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 200


# ── POST /auth/password-reset/confirm ────────────────────────────────────


def test_password_reset_confirm_without_csrf_returns_403(csrf_client):
    csrf_client.get("/auth/csrf-token")
    response = csrf_client.post(
        "/auth/password-reset/confirm",
        json={"token": "sometoken", "new_password": "newsecret12"},
    )
    assert response.status_code == 403


# ── Double-submit integrity check ─────────────────────────────────────────


def test_csrf_header_must_match_cookie(csrf_client):
    """Token from one session must not satisfy a tampered cookie."""
    r = csrf_client.get("/auth/csrf-token")
    real_token = r.json()["csrf_token"]

    # Overwrite the cookie with an attacker-controlled value
    csrf_client.cookies.set("vur_csrf_token", "attacker-value")

    response = csrf_client.post(
        "/auth/register",
        json={"name": "Alice", "email": "a@example.com", "password": "supersecret"},
        headers={"X-CSRF-Token": real_token},
    )
    assert response.status_code == 403


# ── Safe methods are not CSRF-gated ──────────────────────────────────────


def test_get_endpoints_do_not_require_csrf(csrf_client):
    response = csrf_client.get("/health")
    assert response.status_code == 200

    response = csrf_client.get("/auth/csrf-token")
    assert response.status_code == 200
