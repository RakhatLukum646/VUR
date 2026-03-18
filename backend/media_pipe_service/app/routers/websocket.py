"""WebSocket endpoint for real-time sign detection."""

import asyncio
import json
import logging
from typing import Dict

import httpx
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.config import settings
from app.services.ws_auth import verify_ws_token
from app.models.gesture_classifier import GestureClassifier
from app.services.hand_detector import HandDetector
from app.services.sign_buffer import SignBuffer

websocket_router = APIRouter()
logger = logging.getLogger(__name__)

active_connections: Dict[str, WebSocket] = {}
session_languages: Dict[str, str] = {}
hand_detector = HandDetector()
sign_buffer = SignBuffer()
gesture_classifier = GestureClassifier()


def _describe_frame_quality(
    screen_landmarks: list[list[float]] | None,
    detection_confidence: float,
    sign: str | None,
    sign_confidence: float,
    stability: float,
) -> tuple[float, str]:
    if not screen_landmarks:
        return 0.0, "Show one hand in the frame to start detection."

    xs = [point[0] for point in screen_landmarks]
    ys = [point[1] for point in screen_landmarks]
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    area = width * height
    center_x = (max(xs) + min(xs)) / 2
    center_y = (max(ys) + min(ys)) / 2

    if area < 0.04:
        return 0.35, "Move your hand closer to the camera."

    if center_x < 0.2 or center_x > 0.8 or center_y < 0.15 or center_y > 0.85:
        return 0.45, "Center your hand in the frame."

    if not sign or sign_confidence < settings.CONFIDENCE_THRESHOLD:
        return 0.55, "Gesture unclear. Hold one clear hand shape for a moment."

    if detection_confidence < 0.75:
        return 0.6, "Keep your palm visible and improve lighting."

    if stability < 1.0:
        return 0.75, "Hold the gesture steady to confirm the sign."

    return 0.92, "Gesture locked. Continue signing or pause to translate."


@websocket_router.websocket("/ws/sign-detection")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    if not token:
        await websocket.close(code=4401, reason="Missing auth token")
        return
    try:
        verify_ws_token(token)
    except JWTError:
        await websocket.close(code=4403, reason="Invalid auth token")
        return

    await websocket.accept()
    session_id = None

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")
            payload = message.get("payload", {})

            if msg_type == "frame":
                session_id = payload.get("session_id", session_id or "default")
                active_connections[session_id] = websocket
                await handle_frame(websocket, payload, session_id)

            elif msg_type == "command":
                session_id = payload.get("session_id", session_id or "default")
                await handle_command(websocket, payload)

            else:
                await websocket.send_json({
                    "type": "error",
                    "payload": {"message": f"Unknown message type: {msg_type}"},
                })

    except WebSocketDisconnect:
        if session_id and session_id in active_connections:
            del active_connections[session_id]
        if session_id and session_id in session_languages:
            del session_languages[session_id]
    except Exception as e:
        logger.exception("websocket_error session_id=%s", session_id)
        try:
            await websocket.send_json({
                "type": "error",
                "payload": {"message": str(e)},
            })
        except Exception:
            pass


async def handle_frame(websocket: WebSocket, payload: dict, session_id: str):
    """Process video frame, classify gesture, and relay results."""
    try:
        image_b64 = payload.get("image")
        timestamp = payload.get("timestamp", 0)

        if not image_b64:
            await websocket.send_json({
                "type": "detection",
                "payload": {
                    "sign": None,
                    "confidence": 0,
                    "hand_detected": False,
                    "guidance": "Camera frame missing. Check camera access and try again.",
                    "frame_quality": 0,
                    "stability": 0,
                    "sequence_length": 0,
                    "timestamp": timestamp,
                },
            })
            return

        hand_detected, normalized_landmarks, screen_landmarks, handedness, detection_conf = hand_detector.detect(image_b64)

        if not hand_detected:
            # Record no-hand frame; trigger translation if rest boundary reached
            stats = sign_buffer.get_session_stats(session_id)
            buffered_signs = stats["signs_count"]
            should_send = sign_buffer.record_no_hand(session_id)
            guidance = "Show one hand in the frame to start detection."
            if should_send:
                sequence = sign_buffer.commit_sequence(session_id)
                if sequence:
                    guidance = "Pause detected. Sending the captured phrase for translation."
                    lang = session_languages.get(session_id, "ru")
                    asyncio.create_task(
                        send_to_llm_and_relay(session_id, sequence, lang)
                    )
            elif buffered_signs > 0:
                guidance = "Hand lowered. Keep pausing if you want to translate this phrase."

            await websocket.send_json({
                "type": "detection",
                "payload": {
                    "sign": None,
                    "confidence": 0,
                    "hand_detected": False,
                    "guidance": guidance,
                    "frame_quality": 0,
                    "stability": 0,
                    "sequence_length": buffered_signs,
                    "timestamp": timestamp,
                },
            })
            return

        sign, confidence = gesture_classifier.classify(normalized_landmarks)
        is_new = False

        if sign and confidence >= settings.CONFIDENCE_THRESHOLD:
            is_new = sign_buffer.add_sign(session_id, sign, confidence)

        stats = sign_buffer.get_session_stats(session_id)
        frame_quality, guidance = _describe_frame_quality(
            screen_landmarks,
            detection_conf,
            sign,
            confidence,
            stats["stability_progress"],
        )
        commit_ready = False

        if is_new and sign_buffer.should_commit(session_id):
            commit_ready = True
            guidance = "Phrase captured. Sending it for translation."
            frame_quality = max(frame_quality, 0.85)
            committed_count = stats["signs_count"]
            sequence = sign_buffer.commit_sequence(session_id)
            lang = session_languages.get(session_id, "ru")
            asyncio.create_task(
                send_to_llm_and_relay(session_id, sequence, lang)
            )
            stats = {
                **stats,
                "signs_count": committed_count,
                "stability_progress": 0,
            }

        await websocket.send_json({
            "type": "detection",
            "payload": {
                "sign": sign,
                "confidence": confidence,
                "hand_detected": True,
                "landmarks": screen_landmarks,
                "guidance": guidance,
                "frame_quality": frame_quality,
                "stability": stats["stability_progress"],
                "sequence_length": stats["signs_count"],
                "commit_ready": commit_ready,
                "detection_confidence": detection_conf,
                "timestamp": timestamp,
            },
        })

    except Exception as e:
        logger.exception("frame_processing_error session_id=%s", session_id)
        await websocket.send_json({
            "type": "error",
            "payload": {"message": f"Processing error: {str(e)}"},
        })


async def handle_command(websocket: WebSocket, payload: dict):
    action = payload.get("action")
    session_id = payload.get("session_id", "default")

    if action == "start":
        active_connections[session_id] = websocket
        lang = payload.get("language", "ru")
        session_languages[session_id] = lang
        await websocket.send_json({
            "type": "command",
            "payload": {"status": "started", "session_id": session_id, "language": lang},
        })

    elif action == "stop":
        if session_id in active_connections:
            del active_connections[session_id]
        await websocket.send_json({
            "type": "command",
            "payload": {"status": "stopped", "session_id": session_id},
        })

    elif action == "clear":
        sign_buffer.clear_session(session_id)
        await websocket.send_json({
            "type": "command",
            "payload": {"status": "cleared", "session_id": session_id},
        })

    elif action == "translate":
        sequence = sign_buffer.commit_sequence(session_id)
        if sequence:
            lang = session_languages.get(session_id, "ru")
            asyncio.create_task(
                send_to_llm_and_relay(session_id, sequence, lang)
            )
        await websocket.send_json({
            "type": "command",
            "payload": {"status": "translating", "session_id": session_id},
        })


async def send_to_llm_and_relay(session_id: str, sequence: list, language: str = "ru"):
    """Send sign sequence to LLM and relay the translation back via WebSocket."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.LLM_SERVICE_URL}/api/v1/translate",
                json={
                    "sign_sequence": sequence,
                    "session_id": session_id,
                    "context": "",
                    "language": language,
                },
                timeout=15.0,
            )

            if response.status_code == 200:
                result = response.json()
                ws = active_connections.get(session_id)
                if ws:
                    await ws.send_json({
                        "type": "translation",
                        "payload": {
                            "translation": result.get("translation", ""),
                            "confidence": result.get("confidence", 0),
                            "signs": sequence,
                            "session_id": session_id,
                            "processing_time_ms": result.get("processing_time_ms", 0),
                            "fallback": result.get("fallback", False),
                        },
                    })

    except Exception as e:
        logger.exception("llm_relay_failed session_id=%s", session_id)
        ws = active_connections.get(session_id)
        if ws:
            try:
                await ws.send_json({
                    "type": "error",
                    "payload": {"message": f"Translation error: {str(e)}"},
                })
            except Exception:
                pass
