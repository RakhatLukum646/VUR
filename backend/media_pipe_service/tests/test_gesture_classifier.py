"""Tests for gesture classifier and GestureFeatures.

The GestureClassifier uses a two-tier strategy:
  1. MLClassifier (sklearn MLP) when a trained model is present.
  2. Heuristic via GestureFeatures when no model is found.

These tests exercise the public classify() interface and GestureFeatures
directly (replacing the old, now-removed _get_extended_fingers and
_normalize_landmarks helpers).
"""

import pytest
import numpy as np
from app.models.gesture_classifier import GestureClassifier, GestureFeatures


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_landmarks(wrist, tips, pips, default=(0.5, 0.5, 0)):
    """Build a 21-point landmark list with controlled tip/PIP positions.

    wrist  : (x, y, z) for landmark 0
    tips   : dict {landmark_index: (x, y, z)} for finger tips [8,12,16,20]
    pips   : dict {landmark_index: (x, y, z)} for PIP joints [6,10,14,18]
    All remaining landmarks use `default`.
    """
    overrides = {0: wrist, **tips, **pips}
    return [list(overrides.get(i, default)) for i in range(21)]


# ---------------------------------------------------------------------------
# GestureClassifier public interface
# ---------------------------------------------------------------------------

class TestGestureClassifier:

    def setup_method(self):
        self.classifier = GestureClassifier()

    def test_empty_landmarks(self):
        sign, confidence = self.classifier.classify([])
        assert sign is None
        assert confidence == 0.0

    def test_insufficient_landmarks(self):
        sign, confidence = self.classifier.classify([[0, 0, 0]] * 10)
        assert sign is None
        assert confidence == 0.0

    def test_valid_landmarks_returns_float_confidence(self):
        """21 valid landmarks always produce a float confidence in [0, 1]."""
        landmarks = [[0.0, 0.0, 0.0]] * 21
        _sign, confidence = self.classifier.classify(landmarks)
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    def test_random_landmarks_confidence_in_range(self):
        """Random 21×3 landmarks should never raise and confidence is bounded."""
        rng = np.random.default_rng(42)
        for _ in range(20):
            lm = rng.uniform(0, 1, (21, 3)).tolist()
            _sign, conf = self.classifier.classify(lm)
            assert 0.0 <= conf <= 1.0

    def test_classify_returns_str_or_none_for_sign(self):
        """The sign field must be a str or None."""
        lm = [[float(i) * 0.01, float(i) * 0.02, 0.0] for i in range(21)]
        sign, _conf = self.classifier.classify(lm)
        assert sign is None or isinstance(sign, str)


# ---------------------------------------------------------------------------
# GestureFeatures — extension detection
# ---------------------------------------------------------------------------

class TestGestureFeatures:

    def test_closed_fist_fingers_not_extended(self):
        """Tips below their PIP joints → all fingers curled."""
        # tips at y=0.6 (lower in screen), PIPs at y=0.4 (higher → smaller y)
        # In the classifier, idx_ext = tip[1] < pip[1], i.e. tip y must be
        # smaller (higher on screen) than pip y to be extended.
        # Here tip y (0.6) > pip y (0.4) → NOT extended.
        lm = _make_landmarks(
            wrist=(0.5, 0.5, 0),
            tips={8: (0.5, 0.6, 0), 12: (0.5, 0.6, 0), 16: (0.5, 0.6, 0), 20: (0.5, 0.6, 0)},
            pips={6: (0.5, 0.4, 0), 10: (0.5, 0.4, 0), 14: (0.5, 0.4, 0), 18: (0.5, 0.4, 0)},
        )
        f = GestureFeatures(np.array(lm, dtype=float))
        assert f.idx_ext is False
        assert f.mid_ext is False
        assert f.ring_ext is False
        assert f.pink_ext is False

    def test_open_hand_all_fingers_extended(self):
        """Tips above their PIP joints → all fingers extended."""
        # tips at y=0.2 (higher on screen), PIPs at y=0.4
        lm = _make_landmarks(
            wrist=(0.5, 0.8, 0),
            tips={8: (0.5, 0.2, 0), 12: (0.5, 0.2, 0), 16: (0.5, 0.2, 0), 20: (0.5, 0.2, 0)},
            pips={6: (0.5, 0.4, 0), 10: (0.5, 0.4, 0), 14: (0.5, 0.4, 0), 18: (0.5, 0.4, 0)},
        )
        f = GestureFeatures(np.array(lm, dtype=float))
        assert f.idx_ext is True
        assert f.mid_ext is True
        assert f.ring_ext is True
        assert f.pink_ext is True

    def test_extension_vector_length(self):
        """ext vector always has exactly 5 elements."""
        lm = [[0.0] * 3] * 21
        f = GestureFeatures(np.array(lm, dtype=float))
        assert len(f.ext) == 5

    def test_confidence_is_in_range(self):
        """Confidence must be in [0, 1] for any input."""
        rng = np.random.default_rng(7)
        for _ in range(30):
            lm = rng.uniform(0.0, 1.0, (21, 3))
            f = GestureFeatures(lm)
            assert 0.0 <= f.confidence <= 1.0, f"confidence out of range: {f.confidence}"

    def test_curl_ratios_in_range(self):
        """All curl ratios must be clamped to [0, 1]."""
        rng = np.random.default_rng(13)
        for _ in range(20):
            lm = rng.uniform(0.0, 1.0, (21, 3))
            f = GestureFeatures(lm)
            for attr in ("thumb_curl", "idx_curl", "mid_curl", "ring_curl", "pink_curl"):
                val = getattr(f, attr)
                assert 0.0 <= val <= 1.0, f"{attr} out of range: {val}"


class TestMLClassifier:
    def test_returns_none_when_model_unavailable(self):
        """MLClassifier.classify() short-circuits to (None, 0.0) when no
        trained model file is present (the normal state in CI)."""
        from app.models.ml_classifier import MLClassifier

        clf = MLClassifier()
        assert not clf.is_available
        label, conf = clf.classify([[0.0, 0.0, 0.0]] * 21)
        assert label is None
        assert conf == 0.0
