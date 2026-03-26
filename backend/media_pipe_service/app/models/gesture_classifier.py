"""Gesture classifier — S3D temporal model only (RSL word recognition).

Source: https://github.com/ai-forever/easy_sign
Model:  S3D ONNX, 1598 Russian Sign Language classes
Input:  sliding window of S3D_WINDOW_SIZE frames (224×224 RGB)
Output: (rsl_word, confidence) or (None, 0.0)

Frame buffering is handled per-session in the WebSocket router;
this class is stateless and safe to share across sessions.
"""

import logging
import time
from typing import Optional, Tuple

from app.config import settings
from app.models.s3d_classifier import S3DClassifier

logger = logging.getLogger(__name__)


class GestureClassifier:
    """Thin wrapper around S3DClassifier, shared across all WebSocket sessions."""

    def __init__(self):
        t0 = time.perf_counter()

        self._s3d = S3DClassifier(
            model_path=settings.S3D_MODEL_PATH,
            class_list_path=settings.S3D_CLASS_LIST_PATH,
            window_size=settings.S3D_WINDOW_SIZE,
            threshold=settings.S3D_THRESHOLD,
        )

        if settings.USE_S3D:
            try:
                self._s3d.load()
            except Exception as exc:
                logger.warning("s3d_load_failed error=%s — S3D disabled", exc)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        if self._s3d.is_loaded:
            logger.info(
                "classifier_ready model=S3D window=%d threshold=%.2f elapsed_ms=%.1f",
                settings.S3D_WINDOW_SIZE,
                settings.S3D_THRESHOLD,
                elapsed_ms,
            )
        else:
            logger.warning(
                "classifier_ready model=none (S3D failed to load) elapsed_ms=%.1f",
                elapsed_ms,
            )

    @property
    def is_ready(self) -> bool:
        return self._s3d.is_loaded

    def classify(self, frames: list) -> Tuple[Optional[str], float]:
        """Run S3D inference on a window of frames.

        Args:
            frames: List of S3D_WINDOW_SIZE RGB numpy arrays (any size —
                    resized to 224×224 internally).

        Returns:
            (rsl_word, confidence) or (None, 0.0) when model not loaded,
            window not full, or prediction below threshold.
        """
        if not self._s3d.is_loaded:
            return None, 0.0
        result = self._s3d.predict(frames)
        return result if result is not None else (None, 0.0)
