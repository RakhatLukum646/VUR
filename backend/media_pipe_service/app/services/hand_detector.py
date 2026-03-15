"""MediaPipe hand detection service."""

import base64
import io
import numpy as np
import cv2
import mediapipe as mp
from typing import Optional, Tuple, List
from app.config import settings


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
    
    def detect(self, base64_image: str) -> Tuple[bool, Optional[List], Optional[str], float]:
        """
        Detect hand landmarks in image.
        
        Returns:
            Tuple of (hand_detected, landmarks, handedness, confidence)
        """
        try:
            image = self.decode_frame(base64_image)
            
            # Process with MediaPipe
            results = self.hands.process(image)
            
            if not results.multi_hand_landmarks:
                return False, None, None, 0.0
            
            # Get first hand
            hand_landmarks = results.multi_hand_landmarks[0]
            handedness = results.multi_handedness[0].classification[0].label
            confidence = results.multi_handedness[0].classification[0].score
            
            # Extract 21 landmarks [x, y, z]
            landmarks = []
            for landmark in hand_landmarks.landmark:
                landmarks.append([
                    landmark.x,  # Normalized 0-1
                    landmark.y,  # Normalized 0-1
                    landmark.z   # Relative depth
                ])
            
            return True, landmarks, handedness, confidence
            
        except Exception as e:
            print(f"Detection error: {e}")
            return False, None, None, 0.0
    
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
        # Convert landmarks back to MediaPipe format
        hand_landmarks = self.mp_hands.HandLandmark
        
        # Create a copy for drawing
        annotated_image = image.copy()
        
        # Draw using MediaPipe drawing utils
        mp_landmarks = self.mp_hands.HandLandmark
        
        return annotated_image
    
    def close(self):
        """Release resources."""
        self.hands.close()
