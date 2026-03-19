"""Tests targeting uncovered branches to reach 70% coverage threshold."""
import os
import sys
import pickle
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")


# ---------------------------------------------------------------------------
# _describe_frame_quality (websocket.py lines 35-61)
# ---------------------------------------------------------------------------

def test_frame_quality_no_landmarks():
    from app.routers.websocket import _describe_frame_quality

    score, msg = _describe_frame_quality(None, 0.9, "A", 0.8, 1.0)
    assert score == 0.0
    assert "hand" in msg.lower()


def test_frame_quality_hand_too_small():
    from app.routers.websocket import _describe_frame_quality

    # 21 landmarks clustered tightly so area < 0.04
    landmarks = [[0.5, 0.5]] * 21
    score, msg = _describe_frame_quality(landmarks, 0.9, "A", 0.8, 1.0)
    assert score == pytest.approx(0.35)
    assert "closer" in msg.lower()


def test_frame_quality_hand_off_center():
    from app.routers.websocket import _describe_frame_quality

    # Hand big enough (area > 0.04) but centre at x≈0.1 (< 0.2 threshold)
    xs = [0.05, 0.35]
    ys = [0.3, 0.7]
    # Build 21 landmarks within that bounding box; centre_x ≈ 0.2, centre_y ≈ 0.5
    landmarks = [[0.05 + (i % 2) * 0.3, 0.3 + (i % 3) * 0.2] for i in range(21)]
    score, msg = _describe_frame_quality(landmarks, 0.9, "A", 0.8, 1.0)
    assert score == pytest.approx(0.45)
    assert "center" in msg.lower()


def test_frame_quality_unclear_gesture():
    from app.routers.websocket import _describe_frame_quality

    # good size and position, but no sign
    landmarks = [[0.3 + i * 0.01, 0.4 + i * 0.01] for i in range(21)]
    score, msg = _describe_frame_quality(landmarks, 0.9, None, 0.0, 1.0)
    assert score == pytest.approx(0.55)
    assert "unclear" in msg.lower() or "gesture" in msg.lower()


def test_frame_quality_low_detection_confidence():
    from app.routers.websocket import _describe_frame_quality

    landmarks = [[0.3 + i * 0.01, 0.4 + i * 0.01] for i in range(21)]
    score, msg = _describe_frame_quality(landmarks, 0.5, "A", 0.9, 1.0)
    assert score == pytest.approx(0.6)
    assert "lighting" in msg.lower() or "palm" in msg.lower()


def test_frame_quality_unstable():
    from app.routers.websocket import _describe_frame_quality

    landmarks = [[0.3 + i * 0.01, 0.4 + i * 0.01] for i in range(21)]
    score, msg = _describe_frame_quality(landmarks, 0.9, "A", 0.9, 0.5)
    assert score == pytest.approx(0.75)
    assert "hold" in msg.lower() or "steady" in msg.lower()


def test_frame_quality_perfect():
    from app.routers.websocket import _describe_frame_quality

    landmarks = [[0.3 + i * 0.01, 0.4 + i * 0.01] for i in range(21)]
    score, msg = _describe_frame_quality(landmarks, 0.9, "A", 0.9, 1.0)
    assert score == pytest.approx(0.92)
    assert "locked" in msg.lower() or "gesture" in msg.lower()


# ---------------------------------------------------------------------------
# MLClassifier — load failure + classify error paths (lines 63-65, 87-89)
# ---------------------------------------------------------------------------

def test_ml_classifier_load_failure(tmp_path, monkeypatch):
    """_load should swallow errors and leave _pipeline as None."""
    import app.models.ml_classifier as ml_mod

    fake_model = tmp_path / "gesture_model.pkl"
    fake_model.write_bytes(b"not-a-valid-pickle")

    monkeypatch.setattr(ml_mod, "MODEL_PATH", fake_model)

    from app.models.ml_classifier import MLClassifier
    clf = MLClassifier()
    assert not clf.is_available


def test_ml_classifier_classify_error_path():
    """classify should return (None, 0.0) when pipeline.predict_proba raises."""
    from app.models.ml_classifier import MLClassifier

    clf = MLClassifier()
    # inject a broken pipeline
    bad_pipeline = MagicMock()
    bad_pipeline.predict_proba.side_effect = RuntimeError("boom")
    clf._pipeline = bad_pipeline
    clf._classes = ["A", "B"]

    landmarks = [([0.0, 0.0, 0.0]) for _ in range(21)]
    label, confidence = clf.classify(landmarks)
    assert label is None
    assert confidence == 0.0
