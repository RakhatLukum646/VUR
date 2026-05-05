"""Tests for the S3D-based GestureClassifier wrapper.

After the easy_sign (S3D) migration, `GestureClassifier` is a thin,
stateless wrapper around `S3DClassifier`.  It exposes `is_ready` and a
`classify(frames)` method that expects a window of RGB numpy frames.

These tests never touch the real ONNX model — we install the gesture
classifier with `USE_S3D=false` in `conftest.py`, which leaves the
underlying session unloaded, and then exercise the public contract.
For the "loaded" code paths we inject a fake `session_run` so no model
download or onnxruntime import is required.
"""

import numpy as np
import pytest

from app.models.gesture_classifier import GestureClassifier
from app.models.s3d_classifier import S3DClassifier


# ---------------------------------------------------------------------------
# GestureClassifier — public contract when the S3D model is not loaded
# ---------------------------------------------------------------------------

class TestGestureClassifierUnloaded:
    def setup_method(self):
        self.clf = GestureClassifier()

    def test_is_ready_false_when_s3d_not_loaded(self):
        assert self.clf.is_ready is False

    def test_classify_returns_tuple(self):
        result = self.clf.classify([])
        assert isinstance(result, tuple) and len(result) == 2

    def test_classify_empty_frames_returns_none_and_zero(self):
        sign, confidence = self.clf.classify([])
        assert sign is None
        assert confidence == 0.0

    def test_classify_insufficient_frames_returns_none(self):
        frames = [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(2)]
        sign, confidence = self.clf.classify(frames)
        assert sign is None
        assert confidence == 0.0

    def test_classify_confidence_always_float(self):
        sign, confidence = self.clf.classify([])
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    def test_classify_sign_is_str_or_none(self):
        sign, _ = self.clf.classify([])
        assert sign is None or isinstance(sign, str)


# ---------------------------------------------------------------------------
# GestureClassifier — delegates to S3DClassifier when "loaded"
# ---------------------------------------------------------------------------

class TestGestureClassifierLoaded:
    """With a fake ONNX session, the wrapper should forward the top prediction."""

    def _install_fake_session(self, clf: GestureClassifier, logits: np.ndarray,
                              labels: dict[int, str]) -> None:
        """Swap the underlying S3D session for a deterministic fake."""
        s3d = clf._s3d
        s3d._input_name = "input"
        s3d._output_name = "output"
        s3d._labels = labels
        s3d._session_run = lambda outputs, inputs: [logits]

    def test_classify_returns_top_label_when_confidence_above_threshold(self):
        clf = GestureClassifier()
        # 3 classes; "hello" wins by a large margin.
        logits = np.array([[0.1, 5.0, 0.2]], dtype=np.float32)
        self._install_fake_session(clf, logits, {0: "no", 1: "hello", 2: "world"})

        frames = [np.zeros((224, 224, 3), dtype=np.uint8)
                  for _ in range(clf._s3d.window_size)]
        sign, confidence = clf.classify(frames)

        assert sign == "hello"
        assert 0.0 < confidence <= 1.0

    def test_classify_skips_no_gesture_class(self):
        """The special "no" class must never be returned to the caller."""
        clf = GestureClassifier()
        logits = np.array([[10.0, 0.1, 0.1]], dtype=np.float32)  # "no" wins
        self._install_fake_session(clf, logits, {0: "no", 1: "hi", 2: "bye"})

        frames = [np.zeros((224, 224, 3), dtype=np.uint8)
                  for _ in range(clf._s3d.window_size)]
        sign, confidence = clf.classify(frames)

        assert sign is None
        assert confidence == 0.0

    def test_classify_below_threshold_returns_none(self):
        """Uniform logits → max prob ≈ 1/N → below default threshold → None."""
        clf = GestureClassifier()
        clf._s3d.threshold = 0.99
        logits = np.zeros((1, 4), dtype=np.float32)
        self._install_fake_session(clf, logits, {i: f"c{i}" for i in range(4)})

        frames = [np.zeros((224, 224, 3), dtype=np.uint8)
                  for _ in range(clf._s3d.window_size)]
        sign, confidence = clf.classify(frames)

        assert sign is None
        assert confidence == 0.0

    def test_classify_resizes_non_224_frames(self):
        """Frames of arbitrary size must be accepted (internally resized)."""
        clf = GestureClassifier()
        logits = np.array([[0.1, 5.0]], dtype=np.float32)
        self._install_fake_session(clf, logits, {0: "no", 1: "ok"})

        frames = [np.zeros((480, 640, 3), dtype=np.uint8)
                  for _ in range(clf._s3d.window_size)]
        sign, confidence = clf.classify(frames)

        assert sign == "ok"
        assert 0.0 < confidence <= 1.0


# ---------------------------------------------------------------------------
# S3DClassifier — internal helpers
# ---------------------------------------------------------------------------

class TestS3DHelpers:
    """Directly exercise the pure-numpy helpers on S3DClassifier."""

    def test_preprocess_shape_is_1_C_T_H_W(self):
        clf = S3DClassifier(window_size=4)
        frames = [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(4)]
        clip = clf._preprocess(frames)
        assert clip.shape == (1, 3, 4, 224, 224)
        assert clip.dtype == np.float32

    def test_preprocess_normalises_to_unit_range(self):
        clf = S3DClassifier(window_size=2)
        frames = [np.full((224, 224, 3), 255, dtype=np.uint8) for _ in range(2)]
        clip = clf._preprocess(frames)
        assert clip.max() == pytest.approx(1.0)
        assert clip.min() == pytest.approx(1.0)

    def test_preprocess_resizes_large_frames(self):
        clf = S3DClassifier(window_size=2)
        frames = [np.zeros((1080, 1920, 3), dtype=np.uint8) for _ in range(2)]
        clip = clf._preprocess(frames)
        assert clip.shape == (1, 3, 2, 224, 224)

    def test_softmax_rows_sum_to_one(self):
        clf = S3DClassifier()
        x = np.array([[1.0, 2.0, 3.0], [0.0, 0.0, 0.0]])
        probs = clf._softmax(x)
        assert probs.shape == x.shape
        np.testing.assert_allclose(probs.sum(axis=1), [1.0, 1.0])

    def test_softmax_preserves_argmax(self):
        clf = S3DClassifier()
        x = np.array([[0.1, 5.0, 0.2, 1.0]])
        probs = clf._softmax(x)
        assert int(np.argmax(probs)) == 1

    def test_is_loaded_false_by_default(self):
        clf = S3DClassifier()
        assert clf.is_loaded is False

    def test_predict_returns_none_when_not_loaded(self):
        clf = S3DClassifier(window_size=2)
        frames = [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(2)]
        assert clf.predict(frames) is None

    def test_predict_returns_none_when_window_not_full(self):
        clf = S3DClassifier(window_size=8)
        clf._session_run = lambda outputs, inputs: [
            np.array([[10.0, 0.0]], dtype=np.float32)
        ]
        clf._input_name = "in"
        clf._output_name = "out"
        clf._labels = {0: "a", 1: "b"}

        frames = [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(3)]
        assert clf.predict(frames) is None

    def test_predict_catches_inference_errors(self):
        """Any exception inside the session should degrade to None, not crash."""
        clf = S3DClassifier(window_size=2)
        def _boom(outputs, inputs):
            raise RuntimeError("onnx exploded")
        clf._session_run = _boom
        clf._input_name = "in"
        clf._output_name = "out"
        clf._labels = {0: "a"}

        frames = [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(2)]
        assert clf.predict(frames) is None

    def test_predict_falls_back_to_class_n_when_label_missing(self):
        """If the argmax index has no label, a generic name is returned."""
        clf = S3DClassifier(window_size=2, threshold=0.0)
        logits = np.array([[0.1, 8.0]], dtype=np.float32)
        clf._session_run = lambda outputs, inputs: [logits]
        clf._input_name = "in"
        clf._output_name = "out"
        clf._labels = {}  # no labels loaded

        frames = [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(2)]
        result = clf.predict(frames)
        assert result is not None
        label, _ = result
        assert label == "class_1"


# ---------------------------------------------------------------------------
# S3DClassifier — label loading from a tab-separated file
# ---------------------------------------------------------------------------

class TestS3DLabelLoading:
    def test_loads_tab_separated_labels(self, tmp_path):
        path = tmp_path / "classes.txt"
        path.write_text("0\tno\n1\thello\n2\tworld\n", encoding="utf-8")

        clf = S3DClassifier(class_list_path=str(path))
        clf._load_labels()

        assert clf._labels == {0: "no", 1: "hello", 2: "world"}

    def test_skips_malformed_lines(self, tmp_path):
        path = tmp_path / "classes.txt"
        path.write_text(
            "0\tok\n"
            "not-an-int\tbad\n"   # invalid index → skipped
            "no-tab-here\n"        # no tab → skipped
            "3\tthree\n",
            encoding="utf-8",
        )

        clf = S3DClassifier(class_list_path=str(path))
        clf._load_labels()

        assert clf._labels == {0: "ok", 3: "three"}
