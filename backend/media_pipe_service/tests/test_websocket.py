"""Integration tests for the WebSocket sign-detection endpoint."""
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("CONFIDENCE_THRESHOLD", "0.7")
os.environ.setdefault("LLM_SERVICE_URL", "http://llm-service:8002")
os.environ.setdefault("PORT", "8001")
os.environ.setdefault("HOST", "0.0.0.0")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")


def _make_access_token(secret: str = "test-secret") -> str:
    from jose import jwt

    payload = {
        "sub": "user-123",
        "type": "access",
        "jti": "test-jti",
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=15),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture()
def client():
    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c


def test_websocket_rejects_missing_token(client):
    with client.websocket_connect("/ws/sign-detection") as ws:
        # Server closes immediately with 4401 — TestClient raises on receive.
        with pytest.raises(Exception):
            ws.receive_text()


def test_websocket_rejects_invalid_token(client):
    with client.websocket_connect("/ws/sign-detection?token=not-a-valid-jwt") as ws:
        with pytest.raises(Exception):
            ws.receive_text()


def test_websocket_rejects_wrong_token_type(client):
    from jose import jwt

    payload = {
        "sub": "user-123",
        "type": "refresh",  # wrong type
        "jti": "test-jti",
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=15),
    }
    token = jwt.encode(payload, "test-secret", algorithm="HS256")
    with client.websocket_connect(f"/ws/sign-detection?token={token}") as ws:
        with pytest.raises(Exception):
            ws.receive_text()


def test_websocket_accepts_valid_token_and_errors_on_unknown_type(client):
    token = _make_access_token()
    with client.websocket_connect(f"/ws/sign-detection?token={token}") as ws:
        ws.send_text(json.dumps({"type": "unknown_type", "payload": {}}))
        response = json.loads(ws.receive_text())
        assert response["type"] == "error"
        assert "Unknown message type" in response["payload"]["message"]


def test_websocket_command_start_returns_started(client):
    token = _make_access_token()
    with client.websocket_connect(f"/ws/sign-detection?token={token}") as ws:
        ws.send_text(json.dumps({
            "type": "command",
            "payload": {"action": "start", "session_id": "test-session", "language": "en"},
        }))
        response = json.loads(ws.receive_text())
        assert response["type"] == "command"
        assert response["payload"]["status"] == "started"
        assert response["payload"]["session_id"] == "test-session"


def test_websocket_frame_without_image_returns_no_hand_detection(client):
    token = _make_access_token()
    with client.websocket_connect(f"/ws/sign-detection?token={token}") as ws:
        ws.send_text(json.dumps({
            "type": "frame",
            "payload": {"session_id": "test-session", "timestamp": 0},
        }))
        response = json.loads(ws.receive_text())
        assert response["type"] == "detection"
        assert response["payload"]["hand_detected"] is False
