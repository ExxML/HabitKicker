"""Class for detecting habits based on landmark positions"""

import numpy as np
from habitkicker.config.landmark_config import LandmarkConfig

class HabitDetector:
    def __init__(self, max_nail_pulling_distance, max_hair_pulling_distance, max_finger_to_finger_distance):
        # Square the thresholds to avoid square root calculations
        self.NAIL_PULLING_THRESHOLD_SQ = max_nail_pulling_distance * max_nail_pulling_distance
        self.HAIR_PULLING_THRESHOLD_SQ = max_hair_pulling_distance * max_hair_pulling_distance
        self.FINGER_TO_FINGER_THRESHOLD_SQ = max_finger_to_finger_distance * max_finger_to_finger_distance
        self.config = LandmarkConfig()

    def check_nail_biting(self, fingertip_pos, face_landmarks):
        """Check if a fingertip is close to any mouth landmark"""
        for mouth_idx in self.config.MOUTH_LANDMARKS:
            if mouth_idx in face_landmarks:
                mouth_pos = face_landmarks[mouth_idx]
                # Use squared distance to avoid square root calculation
                distance_sq = self._squared_distance(fingertip_pos, mouth_pos)
                if distance_sq < self.NAIL_PULLING_THRESHOLD_SQ:
                    return True, mouth_pos
        return False, None

    def check_hair_pulling(self, thumb_pos, finger_pos, forehead_pos):
        """Check if thumb and another finger are close to a forehead landmark"""
        # Use squared distance to avoid square root calculation
        thumb_to_forehead_sq = self._squared_distance(thumb_pos, forehead_pos)
        if thumb_to_forehead_sq < self.HAIR_PULLING_THRESHOLD_SQ:
            finger_to_forehead_sq = self._squared_distance(finger_pos, forehead_pos)
            finger_to_thumb_sq = self._squared_distance(finger_pos, thumb_pos)
            
            return (finger_to_forehead_sq < self.HAIR_PULLING_THRESHOLD_SQ and 
                   finger_to_thumb_sq < self.FINGER_TO_FINGER_THRESHOLD_SQ)
        return False
        
    def _squared_distance(self, point1, point2):
        """Calculate squared Euclidean distance between two points"""
        # This is faster than np.linalg.norm as it avoids the square root
        dx = point1[0] - point2[0]
        dy = point1[1] - point2[1]
        return dx*dx + dy*dy 