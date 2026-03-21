"""Tests for sign buffer."""

import time

from app.services.sign_buffer import SignBuffer


class TestSignBuffer:
    """Test cases for SignBuffer."""

    def setup_method(self):
        self.buffer = SignBuffer()
        self.session_id = "test-session-123"

    def _stabilize_sign(self, sign: str, confidence: float = 0.9) -> None:
        assert self.buffer.add_sign(self.session_id, sign, confidence) is False
        assert self.buffer.add_sign(self.session_id, sign, confidence) is True

    def test_create_session(self):
        session = self.buffer.get_or_create_session(self.session_id)
        assert session.session_id == self.session_id
        assert len(session.signs) == 0

    def test_add_sign_low_confidence(self):
        assert self.buffer.add_sign(self.session_id, "A", 0.3) is False

    def test_sign_requires_multiple_stable_frames(self):
        first_result = self.buffer.add_sign(self.session_id, "A", 0.9)
        second_result = self.buffer.add_sign(self.session_id, "A", 0.9)

        assert first_result is False
        assert second_result is True
        assert self.buffer.get_sequence(self.session_id) == ["A"]

    def test_add_sign_debounce(self):
        self._stabilize_sign("A")

        result = self.buffer.add_sign(self.session_id, "A", 0.9)

        assert result is False
        assert self.buffer.get_sequence(self.session_id) == ["A"]

    def test_get_sequence_empty(self):
        assert self.buffer.get_sequence("non-existent") == []

    def test_clear_session(self):
        self._stabilize_sign("A")
        self._stabilize_sign("B")

        self.buffer.clear_session(self.session_id)

        assert self.buffer.get_sequence(self.session_id) == []

    def test_commit_sequence(self):
        self._stabilize_sign("H")
        self._stabilize_sign("E")
        self._stabilize_sign("L")

        session = self.buffer.get_or_create_session(self.session_id)
        session.last_sign_time = time.time() - 1
        self._stabilize_sign("L")
        self._stabilize_sign("O")

        session.last_sign_time = time.time() - 5

        assert self.buffer.should_commit(self.session_id) is True
        assert self.buffer.commit_sequence(self.session_id) == ["H", "E", "L", "L", "O"]
        assert self.buffer.get_sequence(self.session_id) == []

    def test_commit_sequence_too_short(self):
        self._stabilize_sign("A")

        session = self.buffer.get_or_create_session(self.session_id)
        session.last_sign_time = time.time() - 5

        assert self.buffer.should_commit(self.session_id) is False

    def test_record_no_hand_clears_pending_sign(self):
        self.buffer.add_sign(self.session_id, "A", 0.9)
        session = self.buffer.get_or_create_session(self.session_id)
        session.signs.append(
            {"sign": "B", "confidence": 0.9, "timestamp": time.time()}
        )

        should_commit = self.buffer.record_no_hand(self.session_id)

        assert should_commit is False
        stats = self.buffer.get_session_stats(self.session_id)
        assert stats["pending_sign"] is None
        assert stats["stability_progress"] == 0

    def test_session_stats(self):
        self._stabilize_sign("A")
        self.buffer.add_sign(self.session_id, "A", 0.9)
        self._stabilize_sign("B")

        stats = self.buffer.get_session_stats(self.session_id)

        assert stats["signs_count"] == 2
        assert stats["unique_signs"] == 2
        assert stats["stability_progress"] == 0
