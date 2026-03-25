"""MediaPipe hand detection service."""

import base64
import io
import numpy as np
import cv2
import mediapipe as mp
from typing import Optional, Tuple, List
from app.config import settings

# Padding fraction applied to each side of the bounding box when cropping.
_CROP_PADDING = 0.20


class HandDetector:
    """MediaPipe hand landmark detector."""
    
    def __init__(self):
        """Initialize MediaPipe Hands."""
        mp_hands = mp.solutions.hands
        
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=settings.MAX_NUM_HANDS,
            min_detection_confidence=settings.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=settings.MIN_TRACKING_CONFIDENCE
        )
        
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_hands = mp_hands
        
    def decode_frame(self, base64_image: str) -> np.ndarray:
        """Decode base64 image to numpy array."""
        try:
            # Remove data URL prefix if present
            if "," in base64_image:
                base64_image = base64_image.split(",")[1]
            
            image_bytes = base64.b64decode(base64_image)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Failed to decode image")
                
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return image_rgb
            
        except Exception as e:
            raise ValueError(f"Image decoding error: {str(e)}")
    
    def detect(self, base64_image: str) -> Tuple[bool, Optional[List], Optional[List], Optional[str], float, Optional[np.ndarray]]:
        """
        Detect hand landmarks in image.

        Returns:
            Tuple of (hand_detected, normalized_landmarks, screen_landmarks,
                      handedness, confidence, hand_crop)
            - normalized_landmarks: wrist-relative unit-scaled coords for ML classifier
            - screen_landmarks: raw 0-1 image coords [[x, y], ...] for overlay drawing
            - hand_crop: RGB uint8 array of the cropped hand region (for ResNet),
                         or None when no hand is detected
        """
        try:
            image = self.decode_frame(base64_image)

            # Process with MediaPipe
            results = self.hands.process(image)

            if not results.multi_hand_landmarks:
                return False, None, None, None, 0.0, None

            # Get first hand
            hand_landmarks = results.multi_hand_landmarks[0]
            handedness = results.multi_handedness[0].classification[0].label
            confidence = results.multi_handedness[0].classification[0].score

            # Raw 0-1 screen coordinates for frontend overlay
            screen_landmarks = []
            raw_for_norm = []
            for landmark in hand_landmarks.landmark:
                screen_landmarks.append([landmark.x, landmark.y])
                raw_for_norm.append([landmark.x, landmark.y, landmark.z])

            # Normalize to wrist-relative, unit-scaled coordinates for classifier
            normalized_landmarks = self.normalize_landmarks(raw_for_norm)

            # Crop the hand region for the ResNet classifier
            hand_crop = self.extract_hand_crop(image, screen_landmarks)

            return True, normalized_landmarks, screen_landmarks, handedness, confidence, hand_crop

        except Exception as e:
            print(f"Detection error: {e}")
            return False, None, None, None, 0.0, None

    def extract_hand_crop(
        self,
        image: np.ndarray,
        screen_landmarks: Optional[List],
        padding: float = _CROP_PADDING,
    ) -> Optional[np.ndarray]:
        """Crop the bounding box around the hand from the full frame.

        Args:
            image: Full RGB frame as a numpy array (H × W × 3).
            screen_landmarks: List of [x, y] coordinates in 0-1 image space.
            padding: Fraction of the bounding-box size to add on each side.

        Returns:
            Cropped RGB numpy array, or None if landmarks are missing/invalid.
        """
        if not screen_landmarks:
            return None

        h, w = image.shape[:2]

        xs = [lm[0] for lm in screen_landmarks]
        ys = [lm[1] for lm in screen_landmarks]

        bw = max(xs) - min(xs)
        bh = max(ys) - min(ys)

        x_min = max(0.0, min(xs) - padding * bw)
        x_max = min(1.0, max(xs) + padding * bw)
        y_min = max(0.0, min(ys) - padding * bh)
        y_max = min(1.0, max(ys) + padding * bh)

        x1, x2 = int(x_min * w), int(x_max * w)
        y1, y2 = int(y_min * h), int(y_max * h)

        if x2 <= x1 or y2 <= y1:
            return None

        return image[y1:y2, x1:x2].copy()
    
    def normalize_landmarks(self, landmarks: List[List[float]]) -> List[List[float]]:
        """
        Normalize landmarks to be relative to wrist position.
        Makes detection invariant to hand position in frame.
        """
        if not landmarks or len(landmarks) < 21:
            return landmarks
        
        # Wrist is landmark 0
        wrist = np.array(landmarks[0])
        
        # Calculate scale (distance from wrist to middle finger MCP - landmark 9)
        middle_finger_mcp = np.array(landmarks[9])
        scale = np.linalg.norm(middle_finger_mcp - wrist)
        
        if scale == 0:
            scale = 1.0
        
        # Normalize all landmarks
        normalized = []
        for lm in landmarks:
            norm_point = (np.array(lm) - wrist) / scale
            normalized.append(norm_point.tolist())
        
        return normalized
    
    def draw_landmarks(self, image: np.ndarray, landmarks: List) -> np.ndarray:
        """Draw landmarks on image for visualization."""
        annotated_image = image.copy()
        h, w = annotated_image.shape[:2]

        # Convert flat list back to pixel coordinates and draw dots + connections
        points = []
        for lm in landmarks:
            px = int(lm[0] * w)
            py = int(lm[1] * h)
            points.append((px, py))
            cv2.circle(annotated_image, (px, py), 4, (0, 255, 0), -1)

        # Draw finger bone connections
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),        # thumb
            (0, 5), (5, 6), (6, 7), (7, 8),          # index
            (0, 9), (9, 10), (10, 11), (11, 12),     # middle
            (0, 13), (13, 14), (14, 15), (15, 16),   # ring
            (0, 17), (17, 18), (18, 19), (19, 20),   # pinky
            (5, 9), (9, 13), (13, 17),               # knuckle bar
        ]
        for start, end in connections:
            if start < len(points) and end < len(points):
                cv2.line(annotated_image, points[start], points[end], (0, 200, 255), 2)

        return annotated_image
    
    def close(self):
        """Release resources."""
        self.hands.close()
