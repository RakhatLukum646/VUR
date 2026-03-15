"""Pydantic models for MediaPipe service."""

from typing import List, Optional, Literal
from pydantic import BaseModel
from datetime import datetime


class HandLandmarks(BaseModel):
    """21 hand landmarks from MediaPipe."""
    landmarks: List[List[float]]  # [[x, y, z], ...] 21 points
    handedness: Optional[str] = None  # "Left" or "Right"


class FrameData(BaseModel):
    """Incoming video frame from client."""
    image: str  # base64 encoded JPEG
    timestamp: int
    session_id: str


class DetectionResult(BaseModel):
    """Output from hand detection."""
    sign: Optional[str] = None  # Detected sign letter/gesture
    confidence: float = 0.0
    hand_detected: bool = False
    landmarks: Optional[List[List[float]]] = None
    timestamp: int


class SignSequence(BaseModel):
    """Accumulated sign sequence."""
    signs: List[str]
    session_id: str
    timestamp: datetime = datetime.utcnow()
    confidence: float = 0.0


class WebSocketMessage(BaseModel):
    """WebSocket message wrapper."""
    type: Literal["frame", "detection", "command", "error"]
    payload: dict


class CommandPayload(BaseModel):
    """Command payload for start/stop."""
    action: Literal["start", "stop", "clear"]
    session_id: str
