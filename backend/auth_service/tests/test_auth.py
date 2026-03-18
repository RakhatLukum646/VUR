import importlib
import sys
from copy import deepcopy
from pathlib import Path

import pyotp
import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class FakeInsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeCollection:
    def __init__(self):
        self.documents: list[dict] = []

    async def find_one(self, query):
        for document in self.documents:
            if self._matches(document, query):
                return deepcopy(document)
        return None

    async def insert_one(self, document):
        stored = deepcopy(document)
        stored.setdefault("_id", ObjectId())
        self.documents.append(stored)
        return FakeInsertOneResult(stored["_id"])

    async def update_one(self, query, update):
        for document in self.documents:
            if self._matches(document, query):
                self._apply_update(document, update)
                return

    async def update_many(self, query, update):
        for document in self.documents:
            if self._matches(document, query):
                self._apply_update(document, update)

    async def delete_many(self, query):
        self.documents = [
            document
            for document in self.documents
            if not self._matches(document, query)
        ]

    async def create_index(self, *args, **kwargs):
        return None

    def insert_seed(self, **document):
        stored = deepcopy(document)
        stored.setdefault("_id", ObjectId())
        self.documents.append(stored)
        return deepcopy(stored)

    @staticmethod
    def _matches(document, query):
        return all(document.get(key) == value for key, value in query.items())

    @staticmethod
    def _apply_update(document, update):
        for key, value in update.get("$set", {}).items():
            document[key] = value
        for key in update.get("$unset", {}):
            document.pop(key, None)


def _reload_app_modules():
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name)

    auth_main = importlib.import_module("app.main")
    auth_router = importlib.import_module("app.routers.auth")
    auth_db = importlib.import_module("app.db")
    auth_dependencies = importlib.import_module("app.dependencies")
    auth_rate_limit = importlib.import_module("app.rate_limit")
    password_reset_service = importlib.import_module(
        "app.services.password_reset_service"
    )
    password_service = importlib.import_module("app.services.password_service")
    session_service = importlib.import_module("app.services.session_service")
    token_service = importlib.import_module("app.services.token_service")
    return {
        "auth_main": auth_main,
        "auth_router": auth_router,
        "auth_db": auth_db,
        "auth_dependencies": auth_dependencies,
        "auth_rate_limit": auth_rate_limit,
        "password_reset_service": password_reset_service,
        "password_service": password_service,
        "session_service": session_service,
        "token_service": token_service,
    }


@pytest.fixture()
def auth_env(monkeypatch):
    monkeypatch.setenv("mongodb_url", "mongodb://localhost:27017")
    monkeypatch.setenv("mongodb_db", "vur_test")
    monkeypatch.setenv("jwt_secret", "test-secret")
    monkeypatch.setenv("email_host", "smtp.example.com")
    monkeypatch.setenv("email_port", "587")
    monkeypatch.setenv("email_user", "noreply@example.com")
    monkeypatch.setenv("email_password", "password")
    monkeypatch.setenv("frontend_url", "http://localhost:5173")


@pytest.fixture()
def client(auth_env, monkeypatch):
    modules = _reload_app_modules()

    fake_users = FakeCollection()
    fake_sessions = FakeCollection()
    fake_password_resets = FakeCollection()
    verification_emails = []
    password_reset_emails = []

    monkeypatch.setattr(modules["auth_db"], "users_collection", fake_users)
    monkeypatch.setattr(modules["auth_db"], "auth_sessions_collection", fake_sessions)
    monkeypatch.setattr(
        modules["auth_db"],
        "password_reset_tokens_collection",
        fake_password_resets,
    )
    monkeypatch.setattr(modules["auth_router"], "users_collection", fake_users)
    monkeypatch.setattr(
        modules["auth_router"],
        "password_reset_tokens_collection",
        fake_password_resets,
    )
    monkeypatch.setattr(
        modules["auth_dependencies"],
        "users_collection",
        fake_users,
    )
    monkeypatch.setattr(
        modules["session_service"],
        "auth_sessions_collection",
        fake_sessions,
    )
    monkeypatch.setattr(
        modules["password_reset_service"],
        "password_reset_tokens_collection",
        fake_password_resets,
    )
    monkeypatch.setattr(
        modules["auth_router"],
        "send_verification_email",
        lambda email, token: verification_emails.append(
            {"email": email, "token": token}
        ),
    )
    monkeypatch.setattr(
        modules["auth_router"],
        "send_password_reset_email",
        lambda email, token: password_reset_emails.append(
            {"email": email, "token": token}
        ),
    )

    async def _noop():
        return None

    monkeypatch.setattr(modules["auth_main"], "ensure_db_ready", _noop)
    modules["auth_rate_limit"].limiter._hits.clear()

    with TestClient(modules["auth_main"].create_app()) as test_client:
        yield {
            "client": test_client,
            "password_resets": fake_password_resets,
            "password_reset_emails": password_reset_emails,
            "password_service": modules["password_service"],
            "sessions": fake_sessions,
            "token_service": modules["token_service"],
            "users": fake_users,
            "verification_emails": verification_emails,
        }


def _seed_user(client, **overrides):
    password = overrides.pop("password", "supersecret")
    document = {
        "name": "Test User",
        "email": "user@example.com",
        "password_hash": client["password_service"].hash_password(password),
        "is_verified": True,
        "verification_token": None,
        "two_factor_enabled": False,
        "two_factor_secret": None,
        "two_factor_recovery_codes": [],
    }
    document.update(overrides)
    return client["users"].insert_seed(**document)


def test_register_creates_user_and_sends_verification_email(client):
    response = client["client"].post(
        "/auth/register",
        json={
            "name": "New User",
            "email": "new@example.com",
            "password": "supersecret",
        },
    )

    assert response.status_code == 200
    assert len(client["users"].documents) == 1
    saved_user = client["users"].documents[0]
    assert saved_user["email"] == "new@example.com"
    assert saved_user["password_hash"] != "supersecret"
    assert saved_user["is_verified"] is False
    assert saved_user["two_factor_recovery_codes"] == []
    assert client["verification_emails"] == [
        {"email": "new@example.com", "token": saved_user["verification_token"]}
    ]


def test_login_requires_verified_email(client):
    _seed_user(client, is_verified=False, verification_token="pending-token")

    response = client["client"].post(
        "/auth/login",
        json={"email": "user@example.com", "password": "supersecret"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Email verification required"
    assert client["sessions"].documents == []


def test_resend_verification_works_without_authentication(client):
    _seed_user(client, is_verified=False, verification_token="old-token")

    response = client["client"].post(
        "/auth/resend-verification",
        json={"email": "user@example.com"},
    )

    assert response.status_code == 200
    assert (
        response.json()["message"]
        == "If that email exists, a verification email has been sent."
    )
    assert len(client["verification_emails"]) == 1
    updated_user = client["users"].documents[0]
    assert updated_user["verification_token"] == client["verification_emails"][0]["token"]
    assert updated_user["verification_token"] != "old-token"


def test_login_sets_httponly_cookies_and_creates_session(client):
    user = _seed_user(client)

    response = client["client"].post(
        "/auth/login",
        json={"email": "user@example.com", "password": "supersecret"},
    )

    assert response.status_code == 200
    data = response.json()
    refresh_payload = client["token_service"].decode_token(
        data["refresh_token"],
        expected_type=client["token_service"].REFRESH_TOKEN_TYPE,
    )

    assert response.cookies.get("vur_access_token") == data["access_token"]
    assert response.cookies.get("vur_refresh_token") == data["refresh_token"]
    assert "HttpOnly" in response.headers["set-cookie"]
    assert data["user"]["id"] == str(user["_id"])
    assert len(client["sessions"].documents) == 1
    assert client["sessions"].documents[0]["jti"] == refresh_payload["jti"]
    assert client["sessions"].documents[0]["revoked_at"] is None


def test_me_accepts_access_cookie_and_rejects_refresh_token(client):
    _seed_user(client)

    login_response = client["client"].post(
        "/auth/login",
        json={"email": "user@example.com", "password": "supersecret"},
    )
    assert login_response.status_code == 200

    ok_response = client["client"].get("/auth/me")
    assert ok_response.status_code == 200
    assert ok_response.json()["email"] == "user@example.com"

    refresh_token = login_response.json()["refresh_token"]
    client["client"].cookies.set("vur_access_token", refresh_token)
    bad_response = client["client"].get("/auth/me")
    assert bad_response.status_code == 401


def test_refresh_rotates_session_and_revokes_previous_token(client):
    _seed_user(client)

    login_response = client["client"].post(
        "/auth/login",
        json={"email": "user@example.com", "password": "supersecret"},
    )
    old_refresh_token = login_response.json()["refresh_token"]
    old_refresh_payload = client["token_service"].decode_token(
        old_refresh_token,
        expected_type=client["token_service"].REFRESH_TOKEN_TYPE,
    )

    refresh_response = client["client"].post("/auth/refresh")

    assert refresh_response.status_code == 200
    new_refresh_token = refresh_response.json()["refresh_token"]
    assert new_refresh_token != old_refresh_token

    new_refresh_payload = client["token_service"].decode_token(
        new_refresh_token,
        expected_type=client["token_service"].REFRESH_TOKEN_TYPE,
    )
    old_session = next(
        document
        for document in client["sessions"].documents
        if document["jti"] == old_refresh_payload["jti"]
    )
    new_session = next(
        document
        for document in client["sessions"].documents
        if document["jti"] == new_refresh_payload["jti"]
    )

    assert old_session["revoked_at"] is not None
    assert new_session["revoked_at"] is None
    assert len(client["sessions"].documents) == 2


def test_password_reset_flow_updates_password_and_revokes_sessions(client):
    user = _seed_user(client)
    client["client"].post(
        "/auth/login",
        json={"email": "user@example.com", "password": "supersecret"},
    )

    request_response = client["client"].post(
        "/auth/password-reset/request",
        json={"email": "user@example.com"},
    )

    assert request_response.status_code == 200
    assert len(client["password_reset_emails"]) == 1
    reset_token = client["password_reset_emails"][0]["token"]
    assert len(client["password_resets"].documents) == 1

    confirm_response = client["client"].post(
        "/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "newsecret"},
    )

    assert confirm_response.status_code == 200
    updated_user = next(
        document
        for document in client["users"].documents
        if document["_id"] == user["_id"]
    )
    assert client["password_service"].verify_password(
        "newsecret",
        updated_user["password_hash"],
    )
    assert not client["password_service"].verify_password(
        "supersecret",
        updated_user["password_hash"],
    )
    assert client["password_resets"].documents == []
    assert all(session["revoked_at"] is not None for session in client["sessions"].documents)


def test_2fa_recovery_code_can_be_used_once(client):
    _seed_user(client)

    login_response = client["client"].post(
        "/auth/login",
        json={"email": "user@example.com", "password": "supersecret"},
    )
    assert login_response.status_code == 200

    setup_response = client["client"].post("/auth/2fa/setup")
    assert setup_response.status_code == 200
    secret = setup_response.json()["secret"]
    code = pyotp.TOTP(secret).now()

    enable_response = client["client"].post("/auth/2fa/enable", json={"code": code})
    assert enable_response.status_code == 200
    recovery_code = enable_response.json()["recovery_codes"][0]

    logout_response = client["client"].post("/auth/logout")
    assert logout_response.status_code == 200

    recovery_login = client["client"].post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "supersecret",
            "recovery_code": recovery_code,
        },
    )
    assert recovery_login.status_code == 200

    reused_code_login = client["client"].post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "supersecret",
            "recovery_code": recovery_code,
        },
    )
    assert reused_code_login.status_code == 401
    assert reused_code_login.json()["detail"] == "Invalid recovery code"


def test_login_rate_limit_returns_429_after_threshold(client):
    for _ in range(10):
        response = client["client"].post(
            "/auth/login",
            json={"email": "missing@example.com", "password": "badpass"},
        )
        assert response.status_code == 401

    limited = client["client"].post(
        "/auth/login",
        json={"email": "missing@example.com", "password": "badpass"},
    )

    assert limited.status_code == 429
