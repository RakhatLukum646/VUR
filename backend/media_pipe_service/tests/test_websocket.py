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
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws/sign-detection"):
            pass
    assert exc_info.value.code == 4401


def test_websocket_rejects_invalid_token(client):
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws/sign-detection?token=not-a-valid-jwt"):
            pass
    assert exc_info.value.code == 4403


def test_websocket_rejects_wrong_token_type(client):
    from jose import jwt
    from starlette.websockets import WebSocketDisconnect

    payload = {
        "sub": "user-123",
        "type": "refresh",  # wrong type
        "jti": "test-jti",
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=15),
    }
    token = jwt.encode(payload, "test-secret", algorithm="HS256")
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/ws/sign-detection?token={token}"):
            pass
    assert exc_info.value.code == 4403


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


def _make_blank_frame_b64() -> str:
    """Encode a small black frame as base64 JPEG.

    Uses numpy + OpenCV, both already required by the service.  The resulting
    image is a valid JPEG that MediaPipe can decode — it will find no hand,
    which is the expected result for a blank frame.
    """
    import base64

    import cv2
    import numpy as np

    frame = np.zeros((64, 64, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", frame)
    return base64.b64encode(buf.tobytes()).decode()


def test_websocket_frame_with_image_exercises_detection_pipeline(client):
    """A frame carrying a valid JPEG runs the full MediaPipe decode → detect
    → buffer path and returns a detection envelope (hand_detected=False for a
    blank image)."""
    token = _make_access_token()
    with client.websocket_connect(f"/ws/sign-detection?token={token}") as ws:
        ws.send_text(json.dumps({
            "type": "frame",
            "payload": {
                "session_id": "test-session",
                "timestamp": 0,
                "image_data": _make_blank_frame_b64(),
            },
        }))
        response = json.loads(ws.receive_text())
        assert response["type"] == "detection"
        assert "hand_detected" in response["payload"]
        assert response["payload"]["hand_detected"] is False


def test_websocket_command_clear_returns_cleared(client):
    token = _make_access_token()
    with client.websocket_connect(f"/ws/sign-detection?token={token}") as ws:
        ws.send_text(json.dumps({
            "type": "command",
            "payload": {"action": "clear", "session_id": "test-session"},
        }))
        response = json.loads(ws.receive_text())
        assert response["type"] == "command"
        assert response["payload"]["status"] == "cleared"
        assert response["payload"]["session_id"] == "test-session"
