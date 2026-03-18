"""Sign sequence buffer management."""

import time
from typing import List, Optional, Dict
from collections import deque
from dataclasses import dataclass, field
from app.config import settings

# Number of consecutive no-hand frames required to treat as a rest position.
# At ~10 fps from the frontend, 3 frames ≈ 300 ms of hands-down.
REST_FRAMES_THRESHOLD = 3
STABILITY_FRAMES_THRESHOLD = 2


@dataclass
class SessionBuffer:
    """Buffer for a single session."""
    session_id: str
    signs: deque = field(default_factory=lambda: deque(maxlen=100))
    last_sign: Optional[str] = None
    last_sign_time: float = field(default_factory=time.time)
    sign_count: Dict[str, int] = field(default_factory=dict)
    # Consecutive frames with no hand detected
    no_hand_streak: int = 0
    pending_sign: Optional[str] = None
    pending_count: int = 0
    pending_confidence_total: float = 0.0


class SignBuffer:
    """Manages sign sequences for multiple sessions."""
    
    def __init__(self):
        self.buffers: Dict[str, SessionBuffer] = {}
        self.min_confidence = settings.CONFIDENCE_THRESHOLD
        self.timeout_ms = settings.SIGN_BUFFER_TIMEOUT_MS
        self.min_sequence_length = settings.MIN_SEQUENCE_LENGTH
        
    def get_or_create_session(self, session_id: str) -> SessionBuffer:
        if session_id not in self.buffers:
            self.buffers[session_id] = SessionBuffer(session_id=session_id)
        return self.buffers[session_id]

    def record_no_hand(self, session_id: str) -> bool:
        """
        Call this each frame when no hand is detected.
        Returns True if the buffer should now be committed (rest boundary reached).
        """
        buffer = self.buffers.get(session_id)
        if not buffer:
            return False

        self._reset_pending(buffer)
        if len(buffer.signs) < self.min_sequence_length:
            return False

        buffer.no_hand_streak += 1
        return buffer.no_hand_streak >= REST_FRAMES_THRESHOLD

    def add_sign(self, session_id: str, sign: str, confidence: float) -> bool:
        """
        Add a detected sign to the buffer.
        Returns True if this is a new unique sign (caller may want to check should_commit).
        """
        if confidence < self.min_confidence:
            return False
        
        if not sign:
            return False
        
        buffer = self.get_or_create_session(session_id)
        current_time = time.time()

        # Reset rest-detection streak: hand is back
        buffer.no_hand_streak = 0
        
        # Debounce: don't add same sign twice in a row too quickly
        if buffer.last_sign == sign:
            time_since_last = (current_time - buffer.last_sign_time) * 1000
            if time_since_last < 500:  # 500ms debounce
                return False

        if buffer.pending_sign == sign:
            buffer.pending_count += 1
            buffer.pending_confidence_total += confidence
        else:
            buffer.pending_sign = sign
            buffer.pending_count = 1
            buffer.pending_confidence_total = confidence

        if buffer.pending_count < STABILITY_FRAMES_THRESHOLD:
            return False

        stable_confidence = buffer.pending_confidence_total / buffer.pending_count
        
        buffer.signs.append({
            "sign": sign,
            "confidence": stable_confidence,
            "timestamp": current_time
        })
        
        buffer.last_sign = sign
        buffer.last_sign_time = current_time
        buffer.sign_count[sign] = buffer.sign_count.get(sign, 0) + 1
        self._reset_pending(buffer)
        
        return True
    
    def get_sequence(self, session_id: str) -> List[str]:
        buffer = self.buffers.get(session_id)
        if not buffer:
            return []
        return [s["sign"] for s in buffer.signs]
    
    def should_commit(self, session_id: str) -> bool:
        """
        True after a timeout with no new signs (fallback timer-based commit).
        Rest-based commit is handled by record_no_hand().
        """
        buffer = self.buffers.get(session_id)
        if not buffer:
            return False
        
        if len(buffer.signs) < self.min_sequence_length:
            return False
        
        time_since_last = (time.time() - buffer.last_sign_time) * 1000
        return time_since_last > self.timeout_ms
    
    def commit_sequence(self, session_id: str) -> List[str]:
        """Commit current sequence and return it. Clears the buffer."""
        buffer = self.buffers.get(session_id)
        if not buffer:
            return []
        
        sequence = [s["sign"] for s in buffer.signs]
        
        buffer.signs.clear()
        buffer.last_sign = None
        buffer.sign_count.clear()
        buffer.no_hand_streak = 0
        self._reset_pending(buffer)
        
        return sequence
    
    def clear_session(self, session_id: str):
        if session_id in self.buffers:
            del self.buffers[session_id]
    
    def get_session_stats(self, session_id: str) -> dict:
        buffer = self.buffers.get(session_id)
        if not buffer:
            return {"signs_count": 0, "unique_signs": 0}
        
        return {
            "signs_count": len(buffer.signs),
            "unique_signs": len(buffer.sign_count),
            "sign_counts": dict(buffer.sign_count),
            "no_hand_streak": buffer.no_hand_streak,
            "pending_sign": buffer.pending_sign,
            "stability_progress": min(
                buffer.pending_count / STABILITY_FRAMES_THRESHOLD,
                1.0,
            ),
        }

    @staticmethod
    def _reset_pending(buffer: SessionBuffer) -> None:
        buffer.pending_sign = None
        buffer.pending_count = 0
        buffer.pending_confidence_total = 0.0
