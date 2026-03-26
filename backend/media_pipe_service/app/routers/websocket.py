"""WebSocket endpoint for real-time sign detection — S3D (RSL) only pipeline."""

import asyncio
import base64
import json
import logging
import os
from collections import deque
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

# Thread pool for S3D inference (CPU-bound, releases GIL).
_workers = min(4, os.cpu_count() or 2)
_inference_executor = ThreadPoolExecutor(max_workers=_workers, thread_name_prefix="s3d")

# Per-session processing gate — drop incoming frame if one is already running.
_processing_sessions: Set[str] = set()
# Buffer for the latest frame that arrived while a session was busy.
_pending_frame: Dict[str, dict] = {}
# Per-session S3D frame deques (accumulate window_size × 224×224 RGB frames).
_s3d_buffers: Dict[str, deque] = {}


def _decode_frame(b64: str) -> np.ndarray:
    """Decode a base64 image string to an RGB numpy array."""
    if "," in b64:
        b64 = b64.split(",")[1]
    img_bytes = base64.b64decode(b64)
    arr = np.frombuffer(img_bytes, np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("Failed to decode image frame.")
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


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

            # Drain stale frames — only the most recent frame matters.
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
        if session_id:
            active_connections.pop(session_id, None)
            session_languages.pop(session_id, None)
            _s3d_buffers.pop(session_id, None)
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
    """Save as pending if inference is already running for this session."""
    if session_id in _processing_sessions:
        _pending_frame[session_id] = payload
        return
    await _process_frame(websocket, payload, session_id)


async def _process_frame(websocket: WebSocket, payload: dict, session_id: str):
    """Decode frame → append to S3D buffer → run inference every window_size frames."""
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

        # Ensure per-session S3D buffer exists.
        if session_id not in _s3d_buffers:
            _s3d_buffers[session_id] = deque(maxlen=settings.S3D_WINDOW_SIZE)

        def _run_inference(img_b64: str, s3d_buf: deque):
            """Blocking: decode + append frame + run S3D when buffer full."""
            image = _decode_frame(img_b64)
            frame_224 = cv2.resize(image, (224, 224))
            s3d_buf.append(frame_224)

            frames_collected = len(s3d_buf)
            if frames_collected < settings.S3D_WINDOW_SIZE:
                # Not enough frames yet.
                return None, 0.0, frames_collected

            sign, confidence = gesture_classifier.classify(list(s3d_buf))
            s3d_buf.clear()
            return sign, confidence, settings.S3D_WINDOW_SIZE

        _processing_sessions.add(session_id)
        try:
            loop = asyncio.get_event_loop()
            sign, confidence, frames_collected = await loop.run_in_executor(
                _inference_executor,
                _run_inference,
                image_b64,
                _s3d_buffers[session_id],
            )
        finally:
            _processing_sessions.discard(session_id)

        # Frames still accumulating — send progress feedback.
        if sign is None and frames_collected < settings.S3D_WINDOW_SIZE:
            progress = frames_collected / settings.S3D_WINDOW_SIZE
            stats = sign_buffer.get_session_stats(session_id)
            await websocket.send_json({
                "type": "detection",
                "payload": {
                    "sign": None,
                    "confidence": 0,
                    "hand_detected": True,
                    "guidance": f"Capturing gesture… ({frames_collected}/{settings.S3D_WINDOW_SIZE} frames)",
                    "frame_quality": round(progress, 2),
                    "stability": progress,
                    "sequence_length": stats["signs_count"],
                    "timestamp": timestamp,
                },
            })
            return

        hand_detected = sign is not None and confidence >= settings.S3D_THRESHOLD

        if not hand_detected:
            stats = sign_buffer.get_session_stats(session_id)
            buffered_signs = stats["signs_count"]
            should_send = sign_buffer.record_no_hand(session_id)

            guidance = "No gesture recognised. Show your hand clearly and hold the sign."
            if should_send:
                sequence = sign_buffer.commit_sequence(session_id)
                if sequence:
                    guidance = "Pause detected. Sending the captured phrase for translation."
                    lang = session_languages.get(session_id, "ru")
                    asyncio.create_task(
                        send_to_llm_and_relay(session_id, sequence, lang)
                    )
            elif buffered_signs > 0:
                guidance = "Hand lowered. Keep pausing to translate this phrase."

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
        commit_ready = False

        if is_new and sign_buffer.should_commit(session_id):
            commit_ready = True
            sequence = sign_buffer.commit_sequence(session_id)
            lang = session_languages.get(session_id, "ru")
            asyncio.create_task(
                send_to_llm_and_relay(session_id, sequence, lang)
            )
            stats = {**stats, "signs_count": stats["signs_count"], "stability_progress": 0}

        await websocket.send_json({
            "type": "detection",
            "payload": {
                "sign": sign,
                "confidence": confidence,
                "hand_detected": True,
                "guidance": "Gesture recognised. Continue signing or pause to translate.",
                "frame_quality": min(confidence, 1.0),
                "stability": stats["stability_progress"],
                "sequence_length": stats["signs_count"],
                "commit_ready": commit_ready,
                "timestamp": timestamp,
            },
        })

    except Exception as e:
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
        active_connections.pop(session_id, None)
        try:
            await websocket.send_json({
                "type": "command",
                "payload": {"status": "stopped", "session_id": session_id},
            })
        except Exception:
            pass

    elif action == "clear":
        sign_buffer.clear_session(session_id)
        _s3d_buffers.pop(session_id, None)
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

    except Exception:
        logger.exception("llm_relay_failed session_id=%s", session_id)
        ws = active_connections.get(session_id)
        if ws:
            try:
                await ws.send_json({
                    "type": "error",
                    "payload": {"message": "Translation service unavailable."},
                })
            except Exception:
                pass
