"""Tests for sign buffer."""

import pytest
import time
from app.services.sign_buffer import SignBuffer, SessionBuffer


class TestSignBuffer:
    """Test cases for SignBuffer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.buffer = SignBuffer()
        self.session_id = "test-session-123"
    
    def test_create_session(self):
        """Test session creation."""
        session = self.buffer.get_or_create_session(self.session_id)
        assert session.session_id == self.session_id
        assert len(session.signs) == 0
    
    def test_add_sign_low_confidence(self):
        """Test that low confidence signs are rejected."""
        result = self.buffer.add_sign(self.session_id, "A", 0.3)
        assert result == False
    
    def test_add_sign_valid(self):
        """Test adding valid sign."""
        result = self.buffer.add_sign(self.session_id, "A", 0.9)
        assert result == True
        
        sequence = self.buffer.get_sequence(self.session_id)
        assert sequence == ["A"]
    
    def test_add_sign_debounce(self):
        """Test that same sign in quick succession is debounced."""
        # Add first sign
        result1 = self.buffer.add_sign(self.session_id, "A", 0.9)
        assert result1 == True
        
        # Try to add same sign immediately
        result2 = self.buffer.add_sign(self.session_id, "A", 0.9)
        assert result2 == False  # Should be debounced
        
        sequence = self.buffer.get_sequence(self.session_id)
        assert len(sequence) == 1
    
    def test_get_sequence_empty(self):
        """Test getting sequence for non-existent session."""
        sequence = self.buffer.get_sequence("non-existent")
        assert sequence == []
    
    def test_clear_session(self):
        """Test clearing session."""
        self.buffer.add_sign(self.session_id, "A", 0.9)
        self.buffer.add_sign(self.session_id, "B", 0.9)
        
        self.buffer.clear_session(self.session_id)
        
        sequence = self.buffer.get_sequence(self.session_id)
        assert sequence == []
    
    def test_commit_sequence(self):
        """Test committing sequence."""
        self.buffer.add_sign(self.session_id, "H", 0.9)
        self.buffer.add_sign(self.session_id, "E", 0.9)
        self.buffer.add_sign(self.session_id, "L", 0.9)
        self.buffer.add_sign(self.session_id, "L", 0.9)
        self.buffer.add_sign(self.session_id, "O", 0.9)
        
        # Manually trigger commit check (simulate timeout)
        session = self.buffer.get_or_create_session(self.session_id)
        session.last_sign_time = time.time() - 5  # 5 seconds ago
        
        should_commit = self.buffer.should_commit(self.session_id)
        assert should_commit == True
        
        sequence = self.buffer.commit_sequence(self.session_id)
        assert sequence == ["H", "E", "L", "L", "O"]
        
        # Buffer should be cleared
        assert len(self.buffer.get_sequence(self.session_id)) == 0
    
    def test_commit_sequence_too_short(self):
        """Test that short sequences don't commit."""
        self.buffer.add_sign(self.session_id, "A", 0.9)
        
        # Wait for timeout
        session = self.buffer.get_or_create_session(self.session_id)
        session.last_sign_time = time.time() - 5
        
        should_commit = self.buffer.should_commit(self.session_id)
        assert should_commit == False  # Too short
    
    def test_session_stats(self):
        """Test getting session statistics."""
        self.buffer.add_sign(self.session_id, "A", 0.9)
        self.buffer.add_sign(self.session_id, "A", 0.9)  # Debounced
        self.buffer.add_sign(self.session_id, "B", 0.9)
        
        stats = self.buffer.get_session_stats(self.session_id)
        assert stats["signs_count"] == 2
        assert stats["unique_signs"] == 2
