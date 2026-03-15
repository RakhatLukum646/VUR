"""Session-based context management for conversations."""
import logging
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """Conversation session."""
    session_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    history: List[dict] = field(default_factory=list)
    current_context: str = ""
    
    def add_interaction(self, signs: List[str], translation: str):
        """Add an interaction to session history."""
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "signs": signs,
            "translation": translation
        })
        self.current_context = translation
        self.last_activity = datetime.utcnow()
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired."""
        expiry = self.last_activity + timedelta(minutes=timeout_minutes)
        return datetime.utcnow() > expiry
    
    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "context": self.current_context,
            "history": self.history[-10:]  # Last 10 interactions
        }


class SessionManager:
    """Manages conversation sessions."""
    
    def __init__(self, max_sessions: int = 1000, timeout_minutes: int = 30):
        """Initialize session manager."""
        self._sessions: Dict[str, Session] = {}
        self._max_sessions = max_sessions
        self._timeout_minutes = timeout_minutes
        logger.info("SessionManager initialized")
    
    def create_session(self) -> str:
        """Create a new session with a generated ID."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = Session(session_id=session_id)
        logger.info(f"Created session: {session_id}")
        return session_id

    def create_session_with_id(self, session_id: str) -> str:
        """Create a session using a specific ID (e.g. from the frontend)."""
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id=session_id)
            logger.info(f"Created session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        session = self._sessions.get(session_id)
        if session and session.is_expired(self._timeout_minutes):
            logger.info(f"Session expired: {session_id}")
            self.delete_session(session_id)
            return None
        return session
    
    def get_context(self, session_id: str) -> str:
        """Get current context for session."""
        session = self.get_session(session_id)
        if session:
            return session.current_context
        return ""
    
    def add_interaction(
        self,
        session_id: str,
        signs: List[str],
        translation: str
    ) -> bool:
        """Add interaction to session."""
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return False
        
        session.add_interaction(signs, translation)
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False
    
    def cleanup_expired(self) -> int:
        """Remove expired sessions. Returns count removed."""
        expired = [
            sid for sid, s in self._sessions.items()
            if s.is_expired(self._timeout_minutes)
        ]
        for sid in expired:
            del self._sessions[sid]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        return len(expired)
    
    def get_stats(self) -> dict:
        """Get session statistics."""
        self.cleanup_expired()
        return {
            "total_sessions": len(self._sessions),
            "max_sessions": self._max_sessions
        }
