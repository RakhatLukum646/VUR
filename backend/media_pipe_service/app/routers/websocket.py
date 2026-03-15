"""WebSocket endpoint for real-time sign detection."""

import json
import asyncio
import httpx
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.hand_detector import HandDetector
from app.services.sign_buffer import SignBuffer
from app.models.gesture_classifier import GestureClassifier
from app.config import settings

websocket_router = APIRouter()

active_connections: Dict[str, WebSocket] = {}
hand_detector = HandDetector()
sign_buffer = SignBuffer()
gesture_classifier = GestureClassifier()


@websocket_router.websocket("/ws/sign-detection")
async def websocket_endpoint(websocket: WebSocket):
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
    except Exception as e:
        print(f"WebSocket error: {e}")
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
                    "timestamp": timestamp,
                },
            })
            return

        hand_detected, landmarks, handedness, detection_conf = hand_detector.detect(image_b64)

        if not hand_detected:
            await websocket.send_json({
                "type": "detection",
                "payload": {
                    "sign": None,
                    "confidence": 0,
                    "hand_detected": False,
                    "timestamp": timestamp,
                },
            })
            return

        normalized_landmarks = hand_detector.normalize_landmarks(landmarks)
        sign, confidence = gesture_classifier.classify(normalized_landmarks)

        if sign and confidence >= settings.CONFIDENCE_THRESHOLD:
            is_new = sign_buffer.add_sign(session_id, sign, confidence)

            if is_new and sign_buffer.should_commit(session_id):
                sequence = sign_buffer.commit_sequence(session_id)
                asyncio.create_task(
                    send_to_llm_and_relay(session_id, sequence)
                )

        await websocket.send_json({
            "type": "detection",
            "payload": {
                "sign": sign,
                "confidence": confidence,
                "hand_detected": True,
                "landmarks": landmarks if settings.DEBUG else None,
                "timestamp": timestamp,
            },
        })

    except Exception as e:
        print(f"Frame processing error: {e}")
        await websocket.send_json({
            "type": "error",
            "payload": {"message": f"Processing error: {str(e)}"},
        })


async def handle_command(websocket: WebSocket, payload: dict):
    action = payload.get("action")
    session_id = payload.get("session_id", "default")

    if action == "start":
        active_connections[session_id] = websocket
        await websocket.send_json({
            "type": "command",
            "payload": {"status": "started", "session_id": session_id},
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
            asyncio.create_task(
                send_to_llm_and_relay(session_id, sequence)
            )
        await websocket.send_json({
            "type": "command",
            "payload": {"status": "translating", "session_id": session_id},
        })


async def send_to_llm_and_relay(session_id: str, sequence: list):
    """Send sign sequence to LLM and relay the translation back via WebSocket."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.LLM_SERVICE_URL}/api/v1/translate",
                json={
                    "sign_sequence": sequence,
                    "session_id": session_id,
                    "context": "",
                    "language": "ru",
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
        print(f"Failed to send to LLM: {e}")
        ws = active_connections.get(session_id)
        if ws:
            try:
                await ws.send_json({
                    "type": "error",
                    "payload": {"message": f"Translation error: {str(e)}"},
                })
            except Exception:
                pass
