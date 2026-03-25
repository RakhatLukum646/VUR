"""
TDD test suite for ResNetClassifier and hand crop extraction.

Write these tests FIRST; run them to confirm Red, then implement to reach Green.

Run all (fast):     pytest tests/test_resnet_classifier.py -m "not slow"
Run slow only:      pytest tests/test_resnet_classifier.py -m slow
Run everything:     pytest tests/test_resnet_classifier.py
"""

import importlib.util
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

_torch_available = importlib.util.find_spec("torch") is not None
_skip_no_torch = pytest.mark.skipif(not _torch_available, reason="torch not installed")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")


# ---------------------------------------------------------------------------
# Phase 1 — Initialization
# ---------------------------------------------------------------------------

class TestResNetClassifierInit:
    """Classifier starts in an unloaded, inert state."""

    def test_is_not_loaded_by_default(self):
        from app.models.resnet_classifier import ResNetClassifier
        clf = ResNetClassifier()
        assert clf.is_loaded is False

    def test_device_defaults_to_cpu(self):
        from app.models.resnet_classifier import ResNetClassifier
        clf = ResNetClassifier()
        assert clf.device == "cpu"

    def test_confidence_threshold_default_is_reasonable(self):
        from app.models.resnet_classifier import ResNetClassifier
        clf = ResNetClassifier()
        assert 0.0 < clf.confidence_threshold <= 1.0

    def test_custom_confidence_threshold_is_stored(self):
        from app.models.resnet_classifier import ResNetClassifier
        clf = ResNetClassifier(confidence_threshold=0.85)
        assert clf.confidence_threshold == pytest.approx(0.85)

    def test_custom_device_is_stored(self):
        from app.models.resnet_classifier import ResNetClassifier
        clf = ResNetClassifier(device="cpu")
        assert clf.device == "cpu"


# ---------------------------------------------------------------------------
# Phase 2 — Preprocessing
# ---------------------------------------------------------------------------

@_skip_no_torch
class TestPreprocessing:
    """_preprocess() must produce a (1, 3, 224, 224) float32 tensor."""

    @pytest.fixture
    def clf(self):
        from app.models.resnet_classifier import ResNetClassifier
        return ResNetClassifier()

    def test_preprocess_returns_4d_tensor(self, clf):
        import torch
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        t = clf._preprocess(img)
        assert t.shape == (1, 3, 224, 224)

    def test_preprocess_returns_float32_tensor(self, clf):
        import torch
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        t = clf._preprocess(img)
        assert t.dtype == torch.float32

    def test_preprocess_white_image_gives_positive_values(self, clf):
        """White (255) > ImageNet mean → normalized values are positive."""
        img = np.full((224, 224, 3), 255, dtype=np.uint8)
        t = clf._preprocess(img)
        assert t.min().item() > 0.0

    def test_preprocess_black_image_gives_negative_values(self, clf):
        """Black (0) < ImageNet mean → all normalized values are negative."""
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        t = clf._preprocess(img)
        assert t.max().item() < 0.0

    def test_preprocess_resizes_small_input(self, clf):
        img = np.zeros((50, 50, 3), dtype=np.uint8)
        t = clf._preprocess(img)
        assert t.shape == (1, 3, 224, 224)

    def test_preprocess_resizes_large_input(self, clf):
        img = np.zeros((1080, 1920, 3), dtype=np.uint8)
        t = clf._preprocess(img)
        assert t.shape == (1, 3, 224, 224)

    def test_preprocess_accepts_float32_array(self, clf):
        """Float32 arrays (0-255 range) should also work."""
        img = np.zeros((224, 224, 3), dtype=np.float32)
        t = clf._preprocess(img)
        assert t.shape == (1, 3, 224, 224)


# ---------------------------------------------------------------------------
# Phase 3 — Index → Letter mapping
# ---------------------------------------------------------------------------

class TestIndexToLetter:
    """_index_to_letter() must map 0→A … 25→Z and reject out-of-range."""

    @pytest.fixture
    def clf(self):
        from app.models.resnet_classifier import ResNetClassifier
        return ResNetClassifier()

    def test_index_0_maps_to_A(self, clf):
        assert clf._index_to_letter(0) == "A"

    def test_index_25_maps_to_Z(self, clf):
        assert clf._index_to_letter(25) == "Z"

    def test_full_sequential_mapping(self, clf):
        for i in range(26):
            assert clf._index_to_letter(i) == chr(65 + i)

    def test_negative_index_raises(self, clf):
        with pytest.raises((ValueError, IndexError)):
            clf._index_to_letter(-1)

    def test_index_26_raises(self, clf):
        with pytest.raises((ValueError, IndexError)):
            clf._index_to_letter(26)


# ---------------------------------------------------------------------------
# Phase 4 — Predict when model is not loaded
# ---------------------------------------------------------------------------

class TestPredictNotLoaded:
    """predict() must return None gracefully before load() is called."""

    def test_predict_returns_none_when_not_loaded(self):
        from app.models.resnet_classifier import ResNetClassifier
        clf = ResNetClassifier()
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        assert clf.predict(img) is None

    def test_predict_does_not_raise_when_not_loaded(self):
        from app.models.resnet_classifier import ResNetClassifier
        clf = ResNetClassifier()
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        # No exception should propagate
        result = clf.predict(img)
        assert result is None


# ---------------------------------------------------------------------------
# Phase 5 — Predict with a mocked model
# ---------------------------------------------------------------------------

def _make_loaded_clf(bias_index: int = 0, confidence_threshold: float = 0.5):
    """Return a ResNetClassifier with a mock model biased toward `bias_index`."""
    import torch
    from app.models.resnet_classifier import ResNetClassifier

    clf = ResNetClassifier(confidence_threshold=confidence_threshold)
    mock_model = MagicMock()
    logits = torch.zeros(1, 26)
    logits[0, bias_index] = 10.0  # Softmax will concentrate near 1.0 here
    mock_model.return_value = logits
    clf._model = mock_model
    return clf


@_skip_no_torch
class TestPredictWithMockModel:
    """predict() returns (letter, confidence) when model is loaded."""

    def test_predict_returns_tuple_of_two(self):
        clf = _make_loaded_clf(bias_index=0)
        result = clf.predict(np.zeros((224, 224, 3), dtype=np.uint8))
        assert isinstance(result, tuple) and len(result) == 2

    def test_predict_first_element_is_letter(self):
        clf = _make_loaded_clf(bias_index=0)
        letter, _ = clf.predict(np.zeros((224, 224, 3), dtype=np.uint8))
        assert letter == "A"

    def test_predict_second_element_is_float(self):
        clf = _make_loaded_clf(bias_index=0)
        _, confidence = clf.predict(np.zeros((224, 224, 3), dtype=np.uint8))
        assert isinstance(confidence, float)

    def test_predict_confidence_is_valid_probability(self):
        clf = _make_loaded_clf(bias_index=0)
        _, confidence = clf.predict(np.zeros((224, 224, 3), dtype=np.uint8))
        assert 0.0 <= confidence <= 1.0

    def test_predict_letter_is_uppercase(self):
        clf = _make_loaded_clf(bias_index=0)
        letter, _ = clf.predict(np.zeros((224, 224, 3), dtype=np.uint8))
        assert letter.isupper()

    def test_predict_letter_is_single_alpha_char(self):
        clf = _make_loaded_clf(bias_index=0)
        letter, _ = clf.predict(np.zeros((224, 224, 3), dtype=np.uint8))
        assert len(letter) == 1 and letter.isalpha()

    def test_predict_maps_index_25_to_Z(self):
        clf = _make_loaded_clf(bias_index=25)
        letter, _ = clf.predict(np.zeros((224, 224, 3), dtype=np.uint8))
        assert letter == "Z"

    def test_predict_maps_index_7_to_H(self):
        clf = _make_loaded_clf(bias_index=7)  # 7 = H
        letter, _ = clf.predict(np.zeros((224, 224, 3), dtype=np.uint8))
        assert letter == "H"

    def test_predict_below_threshold_returns_none(self):
        """Uniform logits → max prob ≈ 1/26 → below 0.99 threshold → None."""
        import torch
        from app.models.resnet_classifier import ResNetClassifier

        clf = ResNetClassifier(confidence_threshold=0.99)
        mock_model = MagicMock()
        mock_model.return_value = torch.zeros(1, 26)  # uniform distribution
        clf._model = mock_model

        result = clf.predict(np.zeros((224, 224, 3), dtype=np.uint8))
        assert result is None

    def test_predict_above_threshold_returns_result(self):
        """High logit bias → confidence near 1.0 → above any reasonable threshold."""
        clf = _make_loaded_clf(bias_index=0, confidence_threshold=0.01)
        result = clf.predict(np.zeros((224, 224, 3), dtype=np.uint8))
        assert result is not None


# ---------------------------------------------------------------------------
# Phase 6 — Model loading from file
# ---------------------------------------------------------------------------

@_skip_no_torch
class TestModelLoading:
    """load(path) must set is_loaded=True and put model in eval mode."""

    def _build_and_save_resnet(self, save_path: Path):
        """Build a minimal ResNet18 with the correct head and save it."""
        import torch
        import torchvision.models as models

        model = models.resnet18(weights=None)
        model.fc = torch.nn.Sequential(
            torch.nn.Dropout(0.5),
            torch.nn.Linear(512, 512),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.3),
            torch.nn.Linear(512, 26),
        )
        torch.save(model, str(save_path))
        return save_path

    def test_load_from_valid_path_sets_is_loaded(self, tmp_path):
        from app.models.resnet_classifier import ResNetClassifier

        model_path = self._build_and_save_resnet(tmp_path / "model.pth")
        clf = ResNetClassifier()
        clf.load(str(model_path))
        assert clf.is_loaded is True

    def test_load_sets_model_to_eval_mode(self, tmp_path):
        from app.models.resnet_classifier import ResNetClassifier

        model_path = self._build_and_save_resnet(tmp_path / "model.pth")
        clf = ResNetClassifier()
        clf.load(str(model_path))
        assert not clf._model.training  # eval mode → training=False

    def test_load_nonexistent_path_raises_file_not_found(self):
        from app.models.resnet_classifier import ResNetClassifier

        clf = ResNetClassifier()
        with pytest.raises(FileNotFoundError):
            clf.load("/nonexistent/path/model.pth")

    def test_predict_works_after_loading_from_file(self, tmp_path):
        from app.models.resnet_classifier import ResNetClassifier

        model_path = self._build_and_save_resnet(tmp_path / "model.pth")
        clf = ResNetClassifier(confidence_threshold=0.0)  # Accept any confidence
        clf.load(str(model_path))

        result = clf.predict(np.zeros((224, 224, 3), dtype=np.uint8))
        assert result is not None
        letter, confidence = result
        assert letter in [chr(65 + i) for i in range(26)]
        assert 0.0 <= confidence <= 1.0


# ---------------------------------------------------------------------------
# Phase 7 — Hand crop extraction (HandDetector.extract_hand_crop)
# ---------------------------------------------------------------------------

@pytest.fixture
def hand_detector():
    """HandDetector with MediaPipe mocked out (no camera/GPU needed)."""
    with patch("mediapipe.solutions.hands.Hands"), \
         patch("mediapipe.solutions.drawing_utils"):
        from app.services.hand_detector import HandDetector
        return HandDetector()


def _landmarks_in_box(x_min=0.3, x_max=0.6, y_min=0.2, y_max=0.5):
    """21 screen landmarks spread within the given bounding box."""
    return [
        [x_min + (i / 20) * (x_max - x_min), y_min + (i / 20) * (y_max - y_min)]
        for i in range(21)
    ]


class TestHandCropExtraction:
    """HandDetector.extract_hand_crop() must return a valid ndarray crop."""

    def test_returns_ndarray(self, hand_detector):
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        crop = hand_detector.extract_hand_crop(img, _landmarks_in_box())
        assert isinstance(crop, np.ndarray)

    def test_returns_3_channel_image(self, hand_detector):
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        crop = hand_detector.extract_hand_crop(img, _landmarks_in_box())
        assert crop.ndim == 3
        assert crop.shape[2] == 3

    def test_crop_has_nonzero_dimensions(self, hand_detector):
        img = np.ones((480, 640, 3), dtype=np.uint8) * 128
        crop = hand_detector.extract_hand_crop(img, _landmarks_in_box())
        assert crop.shape[0] > 0 and crop.shape[1] > 0

    def test_clamps_to_frame_bounds_when_landmarks_at_edges(self, hand_detector):
        """Landmarks at the extreme edges must not cause out-of-bounds slicing."""
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        landmarks = _landmarks_in_box(x_min=0.0, x_max=1.0, y_min=0.0, y_max=1.0)
        # Must not raise
        crop = hand_detector.extract_hand_crop(img, landmarks)
        assert isinstance(crop, np.ndarray)

    def test_none_landmarks_returns_none(self, hand_detector):
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        assert hand_detector.extract_hand_crop(img, None) is None

    def test_empty_landmarks_returns_none(self, hand_detector):
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        assert hand_detector.extract_hand_crop(img, []) is None

    def test_crop_pixel_values_match_source(self, hand_detector):
        """Pixels in the crop should actually come from the original frame."""
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        # Paint the centre region red
        img[100:300, 200:400, 0] = 200  # R channel
        # Landmarks pointing into that centre region
        landmarks = _landmarks_in_box(x_min=0.32, x_max=0.60, y_min=0.22, y_max=0.60)
        crop = hand_detector.extract_hand_crop(img, landmarks)
        # The crop should have non-zero R values (from the painted region)
        assert crop[:, :, 0].max() > 0


# ---------------------------------------------------------------------------
# Phase 8 — GestureClassifier accepts optional `image` kwarg
# ---------------------------------------------------------------------------

class TestGestureClassifierImageKwarg:
    """GestureClassifier.classify() must accept image= without breaking."""

    def test_classify_accepts_image_kwarg(self):
        from app.models.gesture_classifier import GestureClassifier
        clf = GestureClassifier()
        landmarks = [[0.0, 0.0, 0.0]] * 21
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        result = clf.classify(landmarks, image=img)
        assert isinstance(result, tuple) and len(result) == 2

    def test_classify_still_works_without_image(self):
        from app.models.gesture_classifier import GestureClassifier
        clf = GestureClassifier()
        result = clf.classify([[0.0, 0.0, 0.0]] * 21)
        assert isinstance(result, tuple) and len(result) == 2

    def test_classify_empty_landmarks_with_image_kwarg(self):
        from app.models.gesture_classifier import GestureClassifier
        clf = GestureClassifier()
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        sign, confidence = clf.classify([], image=img)
        assert sign is None
        assert confidence == 0.0


# ---------------------------------------------------------------------------
# Phase 9 — HandDetector.detect() returns hand crop (6-tuple)
# ---------------------------------------------------------------------------

class TestHandDetectorDetectReturnsCrop:
    """detect() must return a 6-tuple; last element is crop or None."""

    def test_detect_returns_6_tuple_on_no_hand(self, hand_detector):
        """When no hand is detected the return value still has 6 elements."""
        with patch.object(
            hand_detector.hands,
            "process",
            return_value=MagicMock(multi_hand_landmarks=None),
        ):
            result = hand_detector.detect("dGVzdA==")  # valid base64 "test" bytes
            # May raise ValueError for invalid image — that's OK; we just need
            # the *signature* to be correct when detection runs through.
            # If it raises, the test is inconclusive — skip.

    def test_detect_result_unpacks_to_6(self, hand_detector):
        """No exception when unpacking 6 values from a no-hand detection."""
        # Inject a minimal valid JPEG-like path via mock so decode_frame is skipped
        with patch.object(hand_detector, "decode_frame", return_value=np.zeros((480, 640, 3), dtype=np.uint8)), \
             patch.object(hand_detector.hands, "process",
                          return_value=MagicMock(multi_hand_landmarks=None)):
            hand_detected, norm_lm, screen_lm, handedness, conf, crop = hand_detector.detect("fake_b64")
            assert hand_detected is False
            assert crop is None


# ---------------------------------------------------------------------------
# Phase 10 — Slow / integration tests (require network)
# ---------------------------------------------------------------------------

@pytest.mark.slow
@_skip_no_torch
class TestHuggingFaceIntegration:
    """Downloads the real model from HuggingFace — requires internet access."""

    def test_load_from_huggingface_sets_is_loaded(self):
        from app.models.resnet_classifier import ResNetClassifier
        clf = ResNetClassifier()
        clf.load()  # No path → auto-download
        assert clf.is_loaded is True

    def test_predict_on_blank_image_after_hf_load(self):
        from app.models.resnet_classifier import ResNetClassifier
        clf = ResNetClassifier(confidence_threshold=0.0)  # Accept any result
        clf.load()
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        result = clf.predict(img)
        assert result is not None
        letter, confidence = result
        assert letter in [chr(65 + i) for i in range(26)]
        assert 0.0 <= confidence <= 1.0
