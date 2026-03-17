"""
ML-based gesture classifier using a trained scikit-learn MLP.

Training data format
--------------------
A CSV with columns:
  label, x0, y0, z0, x1, y1, z1, ..., x20, y20, z20   (63 feature columns + 1 label)

The CSV should be placed at:
  backend/media_pipe_service/data/landmarks.csv

To generate training data, use the record_training_data.py script (see scripts/).
To train, run:  python -m app.models.train_classifier

The trained model is saved to:
  backend/media_pipe_service/data/gesture_model.pkl
"""

import logging
import os
import pickle
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent.parent.parent / "data" / "gesture_model.pkl"


class MLClassifier:
    """
    Loads a pre-trained scikit-learn pipeline and classifies gestures.
    Falls back to None if the model file is missing.
    """

    def __init__(self):
        self._pipeline = None
        self._classes: List[str] = []
        self._load()

    def _load(self):
        if not MODEL_PATH.exists():
            logger.info(
                "No trained model found at %s. "
                "Run train_classifier.py to create one. "
                "Falling back to heuristic classifier.",
                MODEL_PATH,
            )
            return

        try:
            with open(MODEL_PATH, "rb") as f:
                bundle = pickle.load(f)
            self._pipeline = bundle["pipeline"]
            self._classes = bundle["classes"]
            logger.info(
                "ML classifier loaded — %d classes: %s",
                len(self._classes),
                self._classes,
            )
        except Exception as e:
            logger.error("Failed to load ML classifier: %s", e)
            self._pipeline = None

    @property
    def is_available(self) -> bool:
        return self._pipeline is not None

    def classify(self, landmarks: List[List[float]]) -> Tuple[Optional[str], float]:
        """
        landmarks: 21 × 3 wrist-relative unit-scaled coordinates.
        Returns (label, confidence) or (None, 0.0) if below threshold.
        """
        if not self.is_available or not landmarks or len(landmarks) < 21:
            return None, 0.0

        features = np.array(landmarks, dtype=float).flatten().reshape(1, -1)

        try:
            proba = self._pipeline.predict_proba(features)[0]
            best_idx = int(np.argmax(proba))
            confidence = float(proba[best_idx])
            label = self._classes[best_idx]
            return label, confidence
        except Exception as e:
            logger.error("ML classification error: %s", e)
            return None, 0.0
