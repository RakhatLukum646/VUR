import importlib
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class FakeInsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeUsersCollection:
    def __init__(self):
        self.documents = []

    async def find_one(self, query):
        for document in self.documents:
            if self._matches(document, query):
                return deepcopy(document)
        return None

    async def insert_one(self, document):
        stored = deepcopy(document)
        stored["_id"] = ObjectId()
        self.documents.append(stored)
        return FakeInsertOneResult(stored["_id"])

    async def update_one(self, query, update):
        for document in self.documents:
            if self._matches(document, query):
                for key, value in update.get("$set", {}).items():
                    document[key] = value
                for key in update.get("$unset", {}):
                    document.pop(key, None)
                return

    def insert_seed_user(self, **overrides):
        document = {
            "_id": ObjectId(),
            "name": "Test User",
            "email": "user@example.com",
            "password_hash": overrides.pop("password_hash"),
            "is_verified": True,
            "verification_token": None,
            "two_factor_enabled": False,
            "two_factor_secret": None,
        }
        document.update(overrides)
        self.documents.append(document)
        return deepcopy(document)

    @staticmethod
    def _matches(document, query):
        return all(document.get(key) == value for key, value in query.items())


@pytest.fixture()
def auth_env(monkeypatch):
    monkeypatch.setenv("mongodb_url", "mongodb://localhost:27017")
    monkeypatch.setenv("mongodb_db", "vur_test")
    monkeypatch.setenv("jwt_secret", "test-secret")
    monkeypatch.setenv("email_host", "smtp.example.com")
    monkeypatch.setenv("email_port", "587")
    monkeypatch.setenv("email_user", "noreply@example.com")
    monkeypatch.setenv("email_password", "password")


@pytest.fixture()
def client(auth_env, monkeypatch):
    auth_main = importlib.import_module("app.main")
    auth_router = importlib.import_module("app.routers.auth")
    auth_dependencies = importlib.import_module("app.dependencies")
    auth_rate_limit = importlib.import_module("app.rate_limit")
    token_service = importlib.import_module("app.services.token_service")

    fake_users = FakeUsersCollection()
    sent_emails = []

    monkeypatch.setattr(auth_router, "users_collection", fake_users)
    monkeypatch.setattr(auth_dependencies, "users_collection", fake_users)
    monkeypatch.setattr(
        auth_router,
        "send_verification_email",
        lambda email, token: sent_emails.append({"email": email, "token": token}),
    )
    auth_rate_limit.limiter._hits.clear()

    with TestClient(auth_main.create_app()) as test_client:
        yield {
            "client": test_client,
            "users": fake_users,
            "emails": sent_emails,
            "tokens": token_service,
            "password_service": importlib.import_module("app.services.password_service"),
        }


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


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
    assert client["emails"] == [
        {"email": "new@example.com", "token": saved_user["verification_token"]}
    ]


def test_login_returns_access_and_refresh_tokens(client):
    password_hash = client["password_service"].hash_password("supersecret")
    client["users"].insert_seed_user(password_hash=password_hash)

    response = client["client"].post(
        "/auth/login",
        json={"email": "user@example.com", "password": "supersecret"},
    )

    assert response.status_code == 200
    data = response.json()
    access_payload = client["tokens"].decode_token(
        data["access_token"],
        expected_type=client["tokens"].ACCESS_TOKEN_TYPE,
    )
    refresh_payload = client["tokens"].decode_token(
        data["refresh_token"],
        expected_type=client["tokens"].REFRESH_TOKEN_TYPE,
    )

    assert access_payload["sub"] == refresh_payload["sub"]
    assert data["access_expires_in"] > 0
    assert data["refresh_expires_in"] > data["access_expires_in"]
    assert data["user"]["email"] == "user@example.com"


def test_me_accepts_access_token_and_rejects_refresh_token(client):
    password_hash = client["password_service"].hash_password("supersecret")
    user = client["users"].insert_seed_user(password_hash=password_hash)

    access_token = client["tokens"].create_access_token(str(user["_id"]))
    refresh_token = client["tokens"].create_refresh_token(str(user["_id"]))

    ok_response = client["client"].get("/auth/me", headers=_auth_headers(access_token))
    bad_response = client["client"].get(
        "/auth/me",
        headers=_auth_headers(refresh_token),
    )

    assert ok_response.status_code == 200
    assert ok_response.json()["email"] == "user@example.com"
    assert bad_response.status_code == 401


def test_refresh_rotates_tokens_and_returns_user(client):
    password_hash = client["password_service"].hash_password("supersecret")
    user = client["users"].insert_seed_user(password_hash=password_hash)
    refresh_token = client["tokens"].create_refresh_token(str(user["_id"]))

    response = client["client"].post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] != refresh_token
    assert data["refresh_token"] != refresh_token
    assert data["user"]["id"] == str(user["_id"])


def test_verify_email_marks_user_as_verified(client):
    response = client["client"].post(
        "/auth/register",
        json={
            "name": "Verifier",
            "email": "verify@example.com",
            "password": "supersecret",
        },
    )
    assert response.status_code == 200

    verification_token = client["emails"][0]["token"]
    verify_response = client["client"].post(
        "/auth/verify-email",
        json={"token": verification_token},
    )

    assert verify_response.status_code == 200
    assert client["users"].documents[0]["is_verified"] is True
    assert "verification_token" not in client["users"].documents[0]


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
