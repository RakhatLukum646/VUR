"""S3D temporal classifier for Russian Sign Language (RSL) word recognition.

Source: https://github.com/ai-forever/easy_sign
Model:  S3D ONNX — trained on ~180k RSL gesture examples (1598 classes)
Input:  sliding window of N frames, each 224×224 RGB, normalized to [0,1]
        tensor shape: (1, C, T, H, W)
Output: RSL word label with confidence score

The model and class list are auto-downloaded on first load from the
ai-forever/easy_sign GitHub repository.
"""

import logging
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_MODEL_URL = "https://raw.githubusercontent.com/ai-forever/easy_sign/main/S3D.onnx"
_CLASS_LIST_URL = "https://raw.githubusercontent.com/ai-forever/easy_sign/main/RSL_class_list.txt"

_DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data"
_DEFAULT_MODEL_PATH = _DEFAULT_DATA_DIR / "S3D.onnx"
_DEFAULT_CLASS_LIST_PATH = _DEFAULT_DATA_DIR / "RSL_class_list.txt"


class S3DClassifier:
    """Wraps the S3D ONNX model from ai-forever/easy_sign.

    Unlike ResNet18 (single-frame), S3D is temporal: it requires a clip of
    ``window_size`` consecutive frames to produce one prediction.

    The frame buffer is intentionally *not* stored here — callers (e.g.
    the WebSocket handler) should maintain per-session deques and pass a
    complete window when ready.  This keeps the classifier stateless and safe
    to share across sessions.
    """

    def __init__(
        self,
        model_path: str = "",
        class_list_path: str = "",
        window_size: int = 32,
        threshold: float = 0.5,
    ):
        self.window_size = window_size
        self.threshold = threshold

        self._model_path = Path(model_path) if model_path else _DEFAULT_MODEL_PATH
        self._class_list_path = (
            Path(class_list_path) if class_list_path else _DEFAULT_CLASS_LIST_PATH
        )

        self._session_run = None  # callable: session.run
        self._input_name: str = ""
        self._output_name: str = ""
        self._labels: dict[int, str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._session_run is not None

    def load(self) -> None:
        """Load the ONNX model, downloading it first if needed."""
        self._ensure_file(_MODEL_URL, self._model_path)
        self._ensure_file(_CLASS_LIST_URL, self._class_list_path)

        try:
            import onnxruntime as rt
        except ImportError as exc:
            raise ImportError(
                "onnxruntime is required for the S3D classifier. "
                "Install it: pip install onnxruntime"
            ) from exc

        try:
            session = rt.InferenceSession(
                str(self._model_path), providers=["CPUExecutionProvider"]
            )
            self._input_name = session.get_inputs()[0].name
            self._output_name = session.get_outputs()[0].name
            self._session_run = session.run
            self._load_labels()
            logger.info(
                "s3d_loaded model=%s classes=%d window=%d threshold=%.2f",
                self._model_path,
                len(self._labels),
                self.window_size,
                self.threshold,
            )
        except Exception as exc:
            logger.error("s3d_load_failed error=%s", exc)
            raise

    def predict(self, frames: list) -> Optional[Tuple[str, float]]:
        """Run inference on a list of ``window_size`` RGB frames.

        Args:
            frames: List of ``window_size`` numpy arrays, each (H, W, 3) uint8.
                    Frames are resized to 224×224 internally if needed.

        Returns:
            ``(label, confidence)`` if confidence ≥ threshold, else ``None``.
        """
        if not self.is_loaded:
            return None
        if len(frames) < self.window_size:
            return None

        try:
            clip = self._preprocess(list(frames)[-self.window_size :])
            output = self._session_run(
                [self._output_name], {self._input_name: clip}
            )[0]
            probs = self._softmax(output)
            probs = np.squeeze(probs)

            top_idx = int(np.argmax(probs))
            top_conf = float(probs[top_idx])

            if top_conf < self.threshold:
                return None

            label = self._labels.get(top_idx, f"class_{top_idx}")
            # Skip the "no gesture" class
            if label in ("no", ""):
                return None

            return label, top_conf

        except Exception as exc:
            logger.error("s3d_predict_failed error=%s", exc)
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _preprocess(self, frames: list) -> np.ndarray:
        """Convert list of RGB frames → (1, C, T, H, W) float32 tensor."""
        resized = []
        for frame in frames:
            if frame.shape[:2] != (224, 224):
                frame = cv2.resize(frame, (224, 224))
            resized.append(frame)

        # Stack to (T, H, W, C), normalise, rearrange to (1, C, T, H, W)
        clip = np.stack(resized, axis=0).astype(np.float32) / 255.0
        # (T, H, W, C) → (C, T, H, W) → (1, C, T, H, W)
        clip = clip.transpose(3, 0, 1, 2)[np.newaxis]
        return clip

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        e = np.exp(x - np.max(x, axis=1, keepdims=True))
        return e / np.sum(e, axis=1, keepdims=True)

    def _load_labels(self) -> None:
        with open(self._class_list_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "\t" in line:
                    idx_str, label = line.split("\t", 1)
                    try:
                        self._labels[int(idx_str)] = label
                    except ValueError:
                        pass

    @staticmethod
    def _ensure_file(url: str, dest: Path) -> None:
        if dest.exists():
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        logger.info("s3d_downloading url=%s → %s", url, dest)
        try:
            urllib.request.urlretrieve(url, str(dest))
            logger.info("s3d_downloaded dest=%s size_mb=%.1f", dest, dest.stat().st_size / 1e6)
        except Exception as exc:
            logger.error("s3d_download_failed url=%s error=%s", url, exc)
            raise
