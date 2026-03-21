import os
import joblib
import numpy as np
import pandas as pd

from typing import Optional, Tuple
from collections import deque, Counter

from app.config import settings
from app.models.feature_extractor import extract_features


MODEL_PATH = os.path.join("app", "models", "asl_rf_model.joblib")


class GestureClassifier:
    def __init__(self):
        self.model = None
        self.feature_names = None
        self.history = deque(maxlen=4)
        self.confidence_threshold = getattr(settings, "CONFIDENCE_THRESHOLD", 0.6)

        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
            print(f"ML model loaded from {MODEL_PATH}")
        else:
            print(f"ML model not found at {MODEL_PATH}")

    def classify(self, landmarks: list) -> Tuple[Optional[str], float]:
        if self.model is None:
            return None, 0.0

        if not landmarks or len(landmarks) < 21:
            return None, 0.0

        try:
            features = extract_features(landmarks)
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return None, 0.0

        if self.feature_names is None:
            self.feature_names = [f"f{i}" for i in range(len(features))]

        df = pd.DataFrame([features], columns=self.feature_names)

        probs = self.model.predict_proba(df)[0]
        idx = int(np.argmax(probs))

        pred = self.model.classes_[idx]
        prob = float(probs[idx])

        print(f"Predicted: {pred}, probability: {prob:.4f}")

        if prob < self.confidence_threshold:
            return None, 0.0

        self.history.append(pred)

        if len(self.history) < self.history.maxlen:
            return None, 0.0

        final = Counter(self.history).most_common(1)[0][0]
        return final, prob