"""WebSocket endpoint for real-time sign detection — ResNet18 only pipeline."""

import asyncio
import base64
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, Set

import cv2
import httpx
import numpy as np
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.config import settings
from app.services.ws_auth import verify_ws_token
from app.models.gesture_classifier import GestureClassifier
from app.services.sign_buffer import SignBuffer

websocket_router = APIRouter()
logger = logging.getLogger(__name__)

active_connections: Dict[str, WebSocket] = {}
session_languages: Dict[str, str] = {}
sign_buffer = SignBuffer()
gesture_classifier = GestureClassifier()

# Thread pool for ResNet18 inference (CPU-bound, releases GIL).
_workers = min(4, os.cpu_count() or 2)
_inference_executor = ThreadPoolExecutor(max_workers=_workers, thread_name_prefix="resnet")

# Per-session processing gate — drop incoming frame if one is already running.
_processing_sessions: Set[str] = set()
# Buffer for the latest frame that arrived while a session was busy.
_pending_frame: Dict[str, dict] = {}


def _decode_frame(b64: str) -> np.ndarray:
    """Decode a base64 image string to a center-cropped RGB numpy array.

    ResNet was trained on hand crops, not full frames.  Taking a square
    center crop keeps the hand large in the 224×224 input and dramatically
    improves recognition of fine-detail signs like O and V.
    """
    if "," in b64:
        b64 = b64.split(",")[1]
    img_bytes = base64.b64decode(b64)
    arr = np.frombuffer(img_bytes, np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("Failed to decode image frame.")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    # Square center crop — assumes the signer holds their hand near the
    # center of the frame.  Crop 60 % of the shorter axis so the hand
    # fills the resulting square rather than being a small speck.
    h, w = rgb.shape[:2]
    side = int(min(h, w) * 0.6)
    cy, cx = h // 2, w // 2
    y1, y2 = cy - side // 2, cy + side // 2
    x1, x2 = cx - side // 2, cx + side // 2
    return rgb[y1:y2, x1:x2]


def _describe_frame_quality(
    sign: Optional[str],
    confidence: float,
    stability: float,
) -> tuple[float, str]:
    if sign is None or confidence < settings.CONFIDENCE_THRESHOLD:
        return 0.5, "Show your hand sign clearly to the camera."
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

            # Drain any stale frames that piled up during inference —
            # only the most recent frame matters for real-time recognition.
            while True:
                try:
                    data = await asyncio.wait_for(
                        websocket.receive_text(), timeout=0.001
                    )
                except asyncio.TimeoutError:
                    break

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
    """Process video frame — save as pending if inference is already running."""
    if session_id in _processing_sessions:
        _pending_frame[session_id] = payload
        return
    await _process_frame(websocket, payload, session_id)


async def _process_frame(websocket: WebSocket, payload: dict, session_id: str):
    """Decode frame → ResNet18 → update sign buffer → send result."""
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

        def _run_inference(img_b64: str):
            """Blocking: decode + ResNet18 predict. Runs in thread pool."""
            image = _decode_frame(img_b64)
            result = gesture_classifier.classify_image(image)
            return result  # (sign, confidence) or (None, 0.0)

        _processing_sessions.add(session_id)
        try:
            loop = asyncio.get_event_loop()
            sign, confidence = await loop.run_in_executor(
                _inference_executor, _run_inference, image_b64
            )
        finally:
            _processing_sessions.discard(session_id)

        hand_detected = sign is not None and confidence >= settings.CONFIDENCE_THRESHOLD

        if not hand_detected:
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

        is_new = sign_buffer.add_sign(session_id, sign, confidence)
        stats = sign_buffer.get_session_stats(session_id)
        frame_quality, guidance = _describe_frame_quality(
            sign, confidence, stats["stability_progress"]
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
            stats = {**stats, "signs_count": committed_count, "stability_progress": 0}

        await websocket.send_json({
            "type": "detection",
            "payload": {
                "sign": sign,
                "confidence": confidence,
                "hand_detected": True,
                "guidance": guidance,
                "frame_quality": frame_quality,
                "stability": stats["stability_progress"],
                "sequence_length": stats["signs_count"],
                "commit_ready": commit_ready,
                "timestamp": timestamp,
            },
        })

    except Exception as e:
        # Client disconnected cleanly — not a real error, nothing to log.
        if type(e).__name__ in ("ClientDisconnected", "ConnectionClosedOK", "ConnectionClosedError"):
            return
        logger.exception("frame_processing_error session_id=%s", session_id)
        try:
            await websocket.send_json({
                "type": "error",
                "payload": {"message": f"Processing error: {str(e)}"},
            })
        except Exception:
            pass
    finally:
        pending = _pending_frame.pop(session_id, None)
        if pending is not None:
            asyncio.create_task(_process_frame(websocket, pending, session_id))


async def handle_command(websocket: WebSocket, payload: dict):
    action = payload.get("action")
    session_id = payload.get("session_id", "default")

    if action == "start":
        active_connections[session_id] = websocket
        lang = payload.get("language", "ru")
        session_languages[session_id] = lang
        try:
            await websocket.send_json({
                "type": "command",
                "payload": {"status": "started", "session_id": session_id, "language": lang},
            })
        except Exception:
            pass

    elif action == "stop":
        if session_id in active_connections:
            del active_connections[session_id]
        try:
            await websocket.send_json({
                "type": "command",
                "payload": {"status": "stopped", "session_id": session_id},
            })
        except Exception:
            pass

    elif action == "clear":
        sign_buffer.clear_session(session_id)
        try:
            await websocket.send_json({
                "type": "command",
                "payload": {"status": "cleared", "session_id": session_id},
            })
        except Exception:
            pass

    elif action == "translate":
        sequence = sign_buffer.commit_sequence(session_id)
        if sequence:
            lang = session_languages.get(session_id, "ru")
            asyncio.create_task(
                send_to_llm_and_relay(session_id, sequence, lang)
            )
        try:
            await websocket.send_json({
                "type": "command",
                "payload": {"status": "translating", "session_id": session_id},
            })
        except Exception:
            pass


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
                    try:
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
                    except Exception:
                        active_connections.pop(session_id, None)

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
