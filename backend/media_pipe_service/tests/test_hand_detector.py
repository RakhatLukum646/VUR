"""Tests for HandDetector (MediaPipe-backed hand landmark extraction).

The MediaPipe solutions are expensive to construct and GPU-sensitive, so
we patch them out and exercise the pure-Python helpers directly:
decoding, normalisation, hand-crop extraction, and the error paths.
"""

import base64
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest


@pytest.fixture
def hand_detector():
    with patch("mediapipe.solutions.hands.Hands"), \
         patch("mediapipe.solutions.drawing_utils"):
        from app.services.hand_detector import HandDetector
        return HandDetector()


def _jpeg_b64(frame: np.ndarray) -> str:
    _, buf = cv2.imencode(".jpg", frame)
    return base64.b64encode(buf.tobytes()).decode()


def _landmarks_in_box(x_min=0.3, x_max=0.6, y_min=0.2, y_max=0.5):
    return [
        [x_min + (i / 20) * (x_max - x_min), y_min + (i / 20) * (y_max - y_min)]
        for i in range(21)
    ]


# ---------------------------------------------------------------------------
# decode_frame
# ---------------------------------------------------------------------------

class TestDecodeFrame:
    def test_decodes_valid_jpeg(self, hand_detector):
        frame = np.zeros((16, 16, 3), dtype=np.uint8)
        decoded = hand_detector.decode_frame(_jpeg_b64(frame))
        assert decoded.shape == (16, 16, 3)
        assert decoded.dtype == np.uint8

    def test_strips_data_url_prefix(self, hand_detector):
        frame = np.zeros((16, 16, 3), dtype=np.uint8)
        data_url = "data:image/jpeg;base64," + _jpeg_b64(frame)
        decoded = hand_detector.decode_frame(data_url)
        assert decoded.shape == (16, 16, 3)

    def test_raises_on_invalid_base64(self, hand_detector):
        with pytest.raises(ValueError):
            hand_detector.decode_frame("!!! not base64 !!!")

    def test_raises_on_non_image_bytes(self, hand_detector):
        payload = base64.b64encode(b"not a jpeg").decode()
        with pytest.raises(ValueError):
            hand_detector.decode_frame(payload)


# ---------------------------------------------------------------------------
# normalize_landmarks
# ---------------------------------------------------------------------------

class TestNormalizeLandmarks:
    def test_returns_input_when_too_few_landmarks(self, hand_detector):
        lm = [[0.0, 0.0, 0.0]] * 5
        assert hand_detector.normalize_landmarks(lm) == lm

    def test_wrist_is_at_origin_after_normalisation(self, hand_detector):
        lm = [[float(i), float(i), 0.0] for i in range(21)]
        norm = hand_detector.normalize_landmarks(lm)
        assert norm[0] == [0.0, 0.0, 0.0]

    def test_scale_falls_back_to_one_when_wrist_equals_mcp(self, hand_detector):
        """Zero-scale case: all landmarks at the same point."""
        lm = [[0.5, 0.5, 0.0]] * 21
        norm = hand_detector.normalize_landmarks(lm)
        # Every normalised landmark must be the zero vector; no division errors.
        for point in norm:
            assert point == [0.0, 0.0, 0.0]

    def test_empty_input_returns_empty(self, hand_detector):
        assert hand_detector.normalize_landmarks([]) == []


# ---------------------------------------------------------------------------
# extract_hand_crop
# ---------------------------------------------------------------------------

class TestExtractHandCrop:
    def test_returns_none_for_empty_landmarks(self, hand_detector):
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        assert hand_detector.extract_hand_crop(img, []) is None

    def test_returns_none_for_none_landmarks(self, hand_detector):
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        assert hand_detector.extract_hand_crop(img, None) is None

    def test_crop_is_3_channel_ndarray(self, hand_detector):
        img = np.ones((480, 640, 3), dtype=np.uint8) * 128
        crop = hand_detector.extract_hand_crop(img, _landmarks_in_box())
        assert isinstance(crop, np.ndarray)
        assert crop.ndim == 3 and crop.shape[2] == 3
        assert crop.shape[0] > 0 and crop.shape[1] > 0

    def test_crop_clamps_to_frame_bounds(self, hand_detector):
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        landmarks = _landmarks_in_box(0.0, 1.0, 0.0, 1.0)
        crop = hand_detector.extract_hand_crop(img, landmarks)
        assert crop is not None and crop.shape[0] <= 480 and crop.shape[1] <= 640

    def test_crop_pixels_come_from_source(self, hand_detector):
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[100:300, 200:400, 0] = 200  # paint R channel in the middle
        landmarks = _landmarks_in_box(0.32, 0.60, 0.22, 0.60)
        crop = hand_detector.extract_hand_crop(img, landmarks)
        assert crop[:, :, 0].max() > 0

    def test_degenerate_bbox_returns_none(self, hand_detector):
        """All landmarks at the same point yield a zero-area crop → None."""
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        landmarks = [[0.5, 0.5] for _ in range(21)]
        assert hand_detector.extract_hand_crop(img, landmarks) is None


# ---------------------------------------------------------------------------
# detect() — the full pipeline, with MediaPipe mocked
# ---------------------------------------------------------------------------

class TestDetect:
    def test_returns_six_tuple_with_no_hand(self, hand_detector):
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        with patch.object(hand_detector.hands, "process",
                          return_value=MagicMock(multi_hand_landmarks=None)):
            result = hand_detector.detect(_jpeg_b64(frame))

        assert isinstance(result, tuple) and len(result) == 6
        hand_detected, norm, screen, handedness, conf, crop = result
        assert hand_detected is False
        assert norm is None and screen is None and handedness is None
        assert conf == 0.0 and crop is None

    def test_returns_landmarks_when_hand_present(self, hand_detector):
        frame = np.zeros((64, 64, 3), dtype=np.uint8)

        # Build a fake MediaPipe result with 21 landmarks.
        fake_landmark = lambda x, y, z: MagicMock(x=x, y=y, z=z)
        landmark_objs = [fake_landmark(0.3 + i * 0.01, 0.4 + i * 0.01, 0.0)
                         for i in range(21)]
        fake_hand = MagicMock(landmark=landmark_objs)
        fake_handedness = MagicMock(
            classification=[MagicMock(label="Right", score=0.87)]
        )
        fake_result = MagicMock(
            multi_hand_landmarks=[fake_hand],
            multi_handedness=[fake_handedness],
        )

        with patch.object(hand_detector.hands, "process", return_value=fake_result):
            hand_detected, norm, screen, handedness, conf, crop = hand_detector.detect(
                _jpeg_b64(frame)
            )

        assert hand_detected is True
        assert handedness == "Right"
        assert conf == pytest.approx(0.87)
        assert len(screen) == 21
        assert len(norm) == 21
        # Wrist should be the origin in normalised space.
        assert norm[0] == [0.0, 0.0, 0.0]
        # Crop should be a valid 3-channel image.
        assert isinstance(crop, np.ndarray) and crop.ndim == 3 and crop.shape[2] == 3

    def test_returns_six_tuple_on_decode_failure(self, hand_detector):
        """Invalid payload is swallowed and returns the empty tuple."""
        hand_detected, norm, screen, handedness, conf, crop = hand_detector.detect(
            "not-base64"
        )
        assert hand_detected is False
        assert (norm, screen, handedness, crop) == (None, None, None, None)
        assert conf == 0.0


# ---------------------------------------------------------------------------
# draw_landmarks and close
# ---------------------------------------------------------------------------

class TestDrawAndClose:
    def test_draw_landmarks_returns_image_of_same_shape(self, hand_detector):
        img = np.zeros((60, 80, 3), dtype=np.uint8)
        landmarks = [[0.25 + i * 0.01, 0.25 + i * 0.01] for i in range(21)]
        annotated = hand_detector.draw_landmarks(img, landmarks)
        assert annotated.shape == img.shape
        # Some dots/lines must have been drawn.
        assert annotated.sum() > 0

    def test_close_delegates_to_mediapipe(self, hand_detector):
        hand_detector.hands.close = MagicMock()
        hand_detector.close()
        hand_detector.hands.close.assert_called_once()
