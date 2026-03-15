"""Tests for gesture classifier."""

import pytest
import numpy as np
from app.models.gesture_classifier import GestureClassifier


class TestGestureClassifier:
    """Test cases for GestureClassifier."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = GestureClassifier()
    
    def test_empty_landmarks(self):
        """Test classification with empty landmarks."""
        sign, confidence = self.classifier.classify([])
        assert sign is None
        assert confidence == 0.0
    
    def test_insufficient_landmarks(self):
        """Test classification with insufficient landmarks."""
        sign, confidence = self.classifier.classify([[0, 0, 0]] * 10)
        assert sign is None
        assert confidence == 0.0
    
    def test_valid_landmarks_format(self):
        """Test that valid landmarks return a result."""
        # Create mock landmarks (all zeros - neutral hand)
        landmarks = [[0, 0, 0] for _ in range(21)]
        
        sign, confidence = self.classifier.classify(landmarks)
        # Should return something (even if None for unclassified gesture)
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
    
    def test_finger_detection_closed_fist(self):
        """Test finger detection for closed fist (all fingers curled)."""
        # Create landmarks simulating closed fist
        landmarks = []
        for i in range(21):
            if i == 0:  # Wrist
                landmarks.append([0.5, 0.5, 0])
            elif i in [8, 12, 16, 20]:  # Finger tips
                landmarks.append([0.5, 0.6, 0])  # Below PIP
            elif i in [6, 10, 14, 18]:  # PIPs
                landmarks.append([0.5, 0.4, 0])  # Above tips
            else:
                landmarks.append([0.5, 0.5, 0])
        
        fingers = self.classifier._get_extended_fingers(np.array(landmarks))
        # All fingers should be curled (False)
        assert fingers[1] == False  # Index
        assert fingers[2] == False  # Middle
        assert fingers[3] == False  # Ring
        assert fingers[4] == False  # Pinky
    
    def test_finger_detection_open_hand(self):
        """Test finger detection for open hand."""
        # Create landmarks simulating open hand
        landmarks = []
        for i in range(21):
            if i == 0:  # Wrist
                landmarks.append([0.5, 0.8, 0])
            elif i in [8, 12, 16, 20]:  # Finger tips
                landmarks.append([0.5, 0.2, 0])  # Above PIPs
            elif i in [6, 10, 14, 18]:  # PIPs
                landmarks.append([0.5, 0.4, 0])  # Below tips
            else:
                landmarks.append([0.5, 0.5, 0])
        
        fingers = self.classifier._get_extended_fingers(np.array(landmarks))
        # All fingers should be extended (True)
        assert fingers[1] == True  # Index
        assert fingers[2] == True  # Middle
        assert fingers[3] == True  # Ring
        assert fingers[4] == True  # Pinky
    
    def test_normalize_landmarks(self):
        """Test landmark normalization."""
        # Create test landmarks with known positions
        landmarks = []
        for i in range(21):
            landmarks.append([float(i) * 0.1, float(i) * 0.05, 0])
        
        normalized = self.classifier._normalize_landmarks(landmarks)
        
        # First landmark (wrist) should be at origin after normalization
        assert abs(normalized[0][0]) < 0.001
        assert abs(normalized[0][1]) < 0.001
        
        # All normalized points should be relative
        for i in range(1, 21):
            assert isinstance(normalized[i], list)
            assert len(normalized[i]) == 3
