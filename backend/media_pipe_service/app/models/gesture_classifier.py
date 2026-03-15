"""Gesture classification using landmarks."""

import numpy as np
from typing import Optional, Tuple
from app.config import settings


class GestureClassifier:
    """
    Simple rule-based classifier for ASL gestures.
    Uses geometric features from hand landmarks.
    """
    
    # Landmark indices
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12
    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20
    
    def __init__(self):
        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD
    
    def classify(self, landmarks: list) -> Tuple[Optional[str], float]:
        """
        Classify gesture from landmarks.
        
        Returns:
            Tuple of (sign, confidence)
        """
        if not landmarks or len(landmarks) < 21:
            return None, 0.0
        
        landmarks = np.array(landmarks)
        
        # Check which fingers are extended
        fingers_extended = self._get_extended_fingers(landmarks)
        
        # Get finger-to-palm relationships
        finger_states = self._get_finger_states(landmarks)
        
        # Classify based on finger patterns
        sign = self._match_pattern(fingers_extended, finger_states, landmarks)
        
        if sign:
            # Calculate confidence based on clarity of pattern
            confidence = self._calculate_confidence(fingers_extended, landmarks)
            return sign, confidence
        
        return None, 0.0
    
    def _get_extended_fingers(self, landmarks: np.ndarray) -> list:
        """Check which fingers are extended."""
        fingers = []
        
        # Thumb (check x distance from pinky MCP)
        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_ip = landmarks[self.THUMB_IP]
        pinky_mcp = landmarks[self.PINKY_MCP]
        thumb_extended = np.linalg.norm(thumb_tip - pinky_mcp) > np.linalg.norm(thumb_ip - pinky_mcp)
        fingers.append(thumb_extended)
        
        # Other 4 fingers (compare tip y to PIP y)
        finger_tips = [self.INDEX_TIP, self.MIDDLE_TIP, self.RING_TIP, self.PINKY_TIP]
        finger_pips = [self.INDEX_PIP, self.MIDDLE_PIP, self.RING_PIP, self.PINKY_PIP]
        
        for tip_idx, pip_idx in zip(finger_tips, finger_pips):
            # Note: y increases downward in image coordinates
            extended = landmarks[tip_idx][1] < landmarks[pip_idx][1]
            fingers.append(extended)
        
        return fingers  # [thumb, index, middle, ring, pinky]
    
    def _get_finger_states(self, landmarks: np.ndarray) -> dict:
        """Get detailed finger states."""
        wrist = landmarks[self.WRIST]
        
        states = {}
        finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']
        
        for i, name in enumerate(finger_names):
            base_idx = i * 4 + 1 if i > 0 else 1
            tip_idx = base_idx + 3 if i > 0 else self.THUMB_TIP
            
            # Calculate if finger is pointing up/down/curled
            tip = landmarks[tip_idx]
            mcp = landmarks[base_idx] if i > 0 else landmarks[self.THUMB_MCP]
            
            # Distance from wrist
            tip_dist = np.linalg.norm(tip - wrist)
            mcp_dist = np.linalg.norm(mcp - wrist)
            
            states[name] = {
                'extended': tip_dist > mcp_dist * 1.5,
                'tip_y': tip[1],
                'tip_x': tip[0]
            }
        
        return states
    
    def _match_pattern(self, fingers: list, states: dict, landmarks: np.ndarray) -> Optional[str]:
        """
        Match finger pattern to ASL letter.
        fingers = [thumb, index, middle, ring, pinky]
        """
        thumb, index, middle, ring, pinky = fingers
        
        # Numbers 0-5
        if fingers == [False, False, False, False, False]:
            return "0"  # Or "O" depending on hand shape
        
        if fingers == [False, True, False, False, False]:
            return "1"
        
        if fingers == [False, True, True, False, False]:
            return "2"
        
        if fingers == [False, True, True, True, False]:
            return "3"
        
        if fingers == [False, True, True, True, True]:
            return "4"
        
        if fingers == [True, True, True, True, True]:
            return "5"
        
        # Letters
        if fingers == [False, True, False, False, False]:
            # Check if index is pointing up (D) or curled (G, X)
            if states['index']['tip_y'] < landmarks[self.INDEX_MCP][1]:
                return "D"
        
        if fingers == [True, False, False, False, False]:
            return "A"
        
        if fingers == [False, True, True, False, False]:
            # Check for U vs V
            index_tip = landmarks[self.INDEX_TIP]
            middle_tip = landmarks[self.MIDDLE_TIP]
            if abs(index_tip[0] - middle_tip[0]) < 0.05:
                return "U"
            return "V"
        
        if fingers == [False, False, False, False, True]:
            return "I"
        
        if fingers == [False, True, True, True, True]:
            return "B"
        
        if fingers == [True, True, True, True, True]:
            # Check if open hand (5, B) or C shape
            return "5"  # Simplified
        
        if not any(fingers[1:]):  # All fingers curled
            if thumb:
                return "A"
            else:
                return "S"
        
        # Rock on / ILY
        if fingers == [False, False, True, False, True]:
            return "ILY"  # I Love You sign
        
        # L shape
        if thumb and index and not middle and not ring and not pinky:
            return "L"
        
        # Y shape  
        if thumb and not index and not middle and not ring and pinky:
            return "Y"
        
        return None
    
    def _calculate_confidence(self, fingers: list, landmarks: np.ndarray) -> float:
        """Calculate confidence score based on clarity."""
        # Higher confidence when pattern is clear
        extended_count = sum(fingers)
        
        # Check landmark stability (distance variance)
        wrist = landmarks[self.WRIST]
        distances = []
        for i in [self.INDEX_TIP, self.MIDDLE_TIP, self.RING_TIP, self.PINKY_TIP]:
            dist = np.linalg.norm(landmarks[i] - wrist)
            distances.append(dist)
        
        variance = np.var(distances)
        
        # Higher confidence for clear, stable patterns
        base_confidence = 0.7 + (0.2 * (1 - min(variance, 1.0)))
        
        return min(base_confidence, 0.95)
