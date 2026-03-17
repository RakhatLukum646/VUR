"""Gesture classification using hand landmarks.

Two-tier strategy
-----------------
1. ML model (MLPClassifier) — loaded from data/gesture_model.pkl when available.
   Trained on 63-feature landmark vectors (21 × [x, y, z]).
   Achieves higher accuracy on full ASL alphabet incl. ambiguous signs.

2. Heuristic fallback — geometry-based rules for ~15 common signs.
   Used automatically when no trained model exists.

To train the ML model:
    cd backend/media_pipe_service
    python scripts/record_training_data.py --label A --samples 200
    # ... repeat for each sign ...
    python scripts/train_classifier.py

All landmarks are expected to be wrist-relative and unit-scaled
(output of HandDetector.normalize_landmarks).
"""

import logging
import numpy as np
from typing import Optional, Tuple
from app.config import settings
from app.models.ml_classifier import MLClassifier

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dist(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def _angle_deg(a: np.ndarray, vertex: np.ndarray, b: np.ndarray) -> float:
    """Angle at `vertex` formed by rays vertex→a and vertex→b (0–180°)."""
    va = a - vertex
    vb = b - vertex
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na < 1e-6 or nb < 1e-6:
        return 0.0
    cos_angle = np.clip(np.dot(va, vb) / (na * nb), -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))


# ---------------------------------------------------------------------------
# GestureFeatures — all derived quantities computed once per frame
# ---------------------------------------------------------------------------

class GestureFeatures:
    """Pre-computed geometric features from a normalized landmark array."""

    def __init__(self, lm: np.ndarray):
        # --- Landmark shortcuts ---
        self.lm = lm
        wrist      = lm[0]
        thumb_cmc  = lm[1];  thumb_mcp = lm[2];  thumb_ip = lm[3];  thumb_tip = lm[4]
        idx_mcp    = lm[5];  idx_pip   = lm[6];  idx_dip  = lm[7];  idx_tip   = lm[8]
        mid_mcp    = lm[9];  mid_pip   = lm[10]; mid_dip  = lm[11]; mid_tip   = lm[12]
        ring_mcp   = lm[13]; ring_pip  = lm[14]; ring_dip = lm[15]; ring_tip  = lm[16]
        pink_mcp   = lm[17]; pink_pip  = lm[18]; pink_dip = lm[19]; pink_tip  = lm[20]

        # --- 5-bit extension vector ---
        # Thumb: extended when tip is clearly to the side of the IP joint
        thumb_abduction = _dist(thumb_tip, pink_mcp) - _dist(thumb_ip, pink_mcp)
        self.thumb_ext = thumb_abduction > 0.0

        # Fingers: tip above PIP in normalized y (negative = up in image coords)
        self.idx_ext  = idx_tip[1]  < idx_pip[1]
        self.mid_ext  = mid_tip[1]  < mid_pip[1]
        self.ring_ext = ring_tip[1] < ring_pip[1]
        self.pink_ext = pink_tip[1] < pink_pip[1]

        self.ext = [self.thumb_ext, self.idx_ext, self.mid_ext,
                    self.ring_ext, self.pink_ext]

        # --- Curl ratios (0 = fully curled, 1 = fully extended) ---
        # Compare tip-to-wrist distance with MCP-to-wrist (rough max extension)
        def curl(tip, mcp):
            tip_d = _dist(tip, wrist)
            mcp_d = _dist(mcp, wrist)
            return float(np.clip(tip_d / (mcp_d * 2.2 + 1e-6), 0.0, 1.0))

        self.thumb_curl = curl(thumb_tip, thumb_mcp)
        self.idx_curl   = curl(idx_tip,   idx_mcp)
        self.mid_curl   = curl(mid_tip,   mid_mcp)
        self.ring_curl  = curl(ring_tip,  ring_mcp)
        self.pink_curl  = curl(pink_tip,  pink_mcp)

        # --- Thumb tuck: how close is the thumb tip to the index MCP? ---
        # Small value → thumb is tucked across the palm (S, A, E …)
        self.thumb_tuck_dist = _dist(thumb_tip, idx_mcp)

        # --- Thumb abduction angle (wrist→thumb_cmc→thumb_tip) ---
        self.thumb_angle = _angle_deg(wrist, thumb_cmc, thumb_tip)

        # --- Index–middle spread (normalized x distance between tips) ---
        self.idx_mid_spread = abs(float(idx_tip[0] - mid_tip[0]))

        # --- Index height above wrist (positive = pointing up in normalized space) ---
        # In wrist-relative coords, negative y = upward
        self.idx_height = -float(idx_tip[1])   # positive when pointing up

        # --- Middle-to-index tip distance (for 3 vs W) ---
        self.mid_idx_tip_dist = _dist(mid_tip, idx_tip)

        # --- Pinky–ring spread ---
        self.pink_ring_spread = abs(float(pink_tip[0] - ring_tip[0]))

        # --- Confidence: mean clarity of each finger's state ---
        def clarity(tip_y, pip_y, expected_ext):
            diff = pip_y - tip_y          # positive → extended
            raw = float(np.clip(0.5 + diff / 0.20, 0.0, 1.0))
            return raw if expected_ext else (1.0 - raw)

        finger_claritys = [
            clarity(idx_tip[1],  idx_pip[1],  self.idx_ext),
            clarity(mid_tip[1],  mid_pip[1],  self.mid_ext),
            clarity(ring_tip[1], ring_pip[1], self.ring_ext),
            clarity(pink_tip[1], pink_pip[1], self.pink_ext),
        ]
        thumb_clarity = float(np.clip(abs(thumb_abduction) / 0.12, 0.0, 1.0))
        if not self.thumb_ext:
            thumb_clarity = 1.0 - thumb_clarity
        finger_claritys.append(thumb_clarity)
        self.confidence = 0.50 + float(np.mean(finger_claritys)) * 0.45


# ---------------------------------------------------------------------------
# GestureClassifier
# ---------------------------------------------------------------------------

class GestureClassifier:
    """
    Gesture classifier with ML-first, heuristic-fallback strategy.
    Expects normalized (wrist-relative, unit-scaled) landmarks.
    """

    def __init__(self):
        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD
        self._ml = MLClassifier()
        if self._ml.is_available:
            logger.info("Using ML classifier (MLP).")
        else:
            logger.info("Using heuristic classifier (no model found).")

    # ------------------------------------------------------------------
    def classify(self, landmarks: list) -> Tuple[Optional[str], float]:
        if not landmarks or len(landmarks) < 21:
            return None, 0.0

        # --- ML path ---------------------------------------------------
        if self._ml.is_available:
            sign, conf = self._ml.classify(landmarks)
            if sign and conf >= self.confidence_threshold:
                return sign, conf
            return None, 0.0

        # --- Heuristic fallback ----------------------------------------
        f = GestureFeatures(np.array(landmarks, dtype=float))
        sign, conf = self._match(f)

        if sign and conf >= self.confidence_threshold:
            return sign, conf
        return None, 0.0

    # ------------------------------------------------------------------
    def _match(self, f: GestureFeatures) -> Tuple[Optional[str], float]:
        """
        Dispatch on the 5-bit extension vector, then apply geometric
        sub-tests to resolve ambiguous cases.
        """
        e = f.ext   # [thumb, idx, mid, ring, pink]
        c = f.confidence

        # ── 0 fingers extended ────────────────────────────────────────
        if e == [False, False, False, False, False]:
            # A: thumb along side of fist (not tucked across palm)
            # S: thumb tucked OVER fingers (tip close to index MCP)
            # O: all fingers curled but rounded (high curl ratio)
            if f.thumb_tuck_dist < 0.25:
                return "S", c
            if f.thumb_ext:
                return "A", c
            # Round curl → O shape
            avg_curl = (f.idx_curl + f.mid_curl + f.ring_curl + f.pink_curl) / 4
            if avg_curl > 0.55:
                return "O", c
            return "A", c

        # ── Thumb only ────────────────────────────────────────────────
        if e == [True, False, False, False, False]:
            return "A", c   # thumb up, fist = A variant

        # ── Index only ────────────────────────────────────────────────
        if e == [False, True, False, False, False]:
            # 1: index pointing up moderately
            # D: index pointing very high, other fingers curled into circle
            # G: index pointing sideways (low height)
            if f.idx_height > 1.2:
                return "D", c
            if f.idx_height > 0.4:
                return "1", c
            return "G", c

        # ── Pinky only ────────────────────────────────────────────────
        if e == [False, False, False, False, True]:
            return "I", c

        # ── Thumb + pinky ─────────────────────────────────────────────
        if e == [True, False, False, False, True]:
            return "Y", c

        # ── Thumb + index ─────────────────────────────────────────────
        if e == [True, True, False, False, False]:
            # L: classic L-shape, index high and thumb spread
            if f.idx_height > 0.5 and f.thumb_angle > 40:
                return "L", c
            return "L", c   # no other common sign shares this pattern

        # ── Index + middle ────────────────────────────────────────────
        if e == [False, True, True, False, False]:
            # 2: both up, fingers visibly apart (spread > threshold)
            # V: peace sign — fingers spread, wider than 2
            # U: fingers together, parallel
            if f.idx_mid_spread > 0.22:
                return "V", c
            if f.idx_mid_spread > 0.10:
                return "2", c
            return "U", c

        # ── Middle + pinky (ILY variant) ──────────────────────────────
        if e == [False, False, True, False, True]:
            return "ILY", c

        # ── Index + middle + ring ─────────────────────────────────────
        if e == [False, True, True, True, False]:
            # 3: three up; W has ring finger spread farther out
            # W: thumb also partially extended or ring is very spread
            if f.thumb_curl > 0.5 and f.pink_ring_spread < 0.15:
                return "3", c
            return "W", c

        # ── Index + ring + pinky ──────────────────────────────────────
        if e == [False, True, False, True, True]:
            return "W", c

        # ── All four fingers (no thumb) ───────────────────────────────
        if e == [False, True, True, True, True]:
            # B: thumb tucked, all 4 fingers straight up together
            # 4: thumb is spread out to the side
            if f.thumb_tuck_dist < 0.35:
                return "B", c
            return "4", c

        # ── Thumb + middle + ring + pinky (index curled) ──────────────
        if e == [True, False, True, True, True]:
            return "4", c   # ASL 4 variant with thumb out

        # ── All five fingers ──────────────────────────────────────────
        if e == [True, True, True, True, True]:
            # 5: open hand, fingers spread
            # B-open / flat-B: fingers together, thumb alongside
            if f.idx_mid_spread > 0.12 or f.thumb_angle > 35:
                return "5", c
            return "B", c

        # ── Thumb + index + middle ────────────────────────────────────
        if e == [True, True, True, False, False]:
            return "K", c

        # ── Thumb + index + middle + ring ─────────────────────────────
        if e == [True, True, True, True, False]:
            # Approximation for H / 4-open
            return "H", c

        # ── Thumb + index + pinky ─────────────────────────────────────
        if e == [True, True, False, False, True]:
            return "ILY", c  # I Love You

        return None, 0.0
