"""Sign sequence buffer management."""

import time
from typing import List, Optional, Dict
from collections import deque
from dataclasses import dataclass, field
from app.config import settings


@dataclass
class SessionBuffer:
    """Buffer for a single session."""
    session_id: str
    signs: deque = field(default_factory=lambda: deque(maxlen=100))
    last_sign: Optional[str] = None
    last_sign_time: float = field(default_factory=time.time)
    sign_count: Dict[str, int] = field(default_factory=dict)


class SignBuffer:
    """Manages sign sequences for multiple sessions."""
    
    def __init__(self):
        self.buffers: Dict[str, SessionBuffer] = {}
        self.min_confidence = settings.CONFIDENCE_THRESHOLD
        self.timeout_ms = settings.SIGN_BUFFER_TIMEOUT_MS
        self.min_sequence_length = settings.MIN_SEQUENCE_LENGTH
        
    def get_or_create_session(self, session_id: str) -> SessionBuffer:
        """Get existing session or create new one."""
        if session_id not in self.buffers:
            self.buffers[session_id] = SessionBuffer(session_id=session_id)
        return self.buffers[session_id]
    
    def add_sign(self, session_id: str, sign: str, confidence: float) -> bool:
        """
        Add a detected sign to the buffer.
        Returns True if this is a new unique sign.
        """
        if confidence < self.min_confidence:
            return False
        
        if not sign:
            return False
        
        buffer = self.get_or_create_session(session_id)
        current_time = time.time()
        
        # Debounce: don't add same sign twice in a row too quickly
        if buffer.last_sign == sign:
            time_since_last = (current_time - buffer.last_sign_time) * 1000
            if time_since_last < 500:  # 500ms debounce
                return False
        
        # Add sign to buffer
        buffer.signs.append({
            "sign": sign,
            "confidence": confidence,
            "timestamp": current_time
        })
        
        buffer.last_sign = sign
        buffer.last_sign_time = current_time
        buffer.sign_count[sign] = buffer.sign_count.get(sign, 0) + 1
        
        return True
    
    def get_sequence(self, session_id: str) -> List[str]:
        """Get current sign sequence for session."""
        buffer = self.buffers.get(session_id)
        if not buffer:
            return []
        return [s["sign"] for s in buffer.signs]
    
    def should_commit(self, session_id: str) -> bool:
        """
        Check if we should commit the current sequence.
        This happens after a timeout with no new signs.
        """
        buffer = self.buffers.get(session_id)
        if not buffer:
            return False
        
        if len(buffer.signs) < self.min_sequence_length:
            return False
        
        time_since_last = (time.time() - buffer.last_sign_time) * 1000
        return time_since_last > self.timeout_ms
    
    def commit_sequence(self, session_id: str) -> List[str]:
        """
        Commit current sequence and return it.
        Clears the buffer after committing.
        """
        buffer = self.buffers.get(session_id)
        if not buffer:
            return []
        
        sequence = [s["sign"] for s in buffer.signs]
        
        # Clear buffer
        buffer.signs.clear()
        buffer.last_sign = None
        buffer.sign_count.clear()
        
        return sequence
    
    def clear_session(self, session_id: str):
        """Clear a specific session buffer."""
        if session_id in self.buffers:
            del self.buffers[session_id]
    
    def get_session_stats(self, session_id: str) -> dict:
        """Get statistics for a session."""
        buffer = self.buffers.get(session_id)
        if not buffer:
            return {"signs_count": 0, "unique_signs": 0}
        
        return {
            "signs_count": len(buffer.signs),
            "unique_signs": len(buffer.sign_count),
            "sign_counts": dict(buffer.sign_count)
        }
