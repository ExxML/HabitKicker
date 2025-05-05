"""Class for detecting habits based on landmark positions"""

import numpy as np
from config.landmark_config import LandmarkConfig

class HabitDetector:
    def __init__(self, max_nail_pulling_distance, max_hair_pulling_distance):
        self.NAIL_PULLING_THRESHOLD = max_nail_pulling_distance
        self.HAIR_PULLING_THRESHOLD = max_hair_pulling_distance
        self.config = LandmarkConfig()

    def check_nail_biting(self, fingertip_pos, face_landmarks):
        """Check if a fingertip is close to any mouth landmark"""
        for mouth_idx in self.config.MOUTH_LANDMARKS:
            if mouth_idx in face_landmarks:
                mouth_pos = face_landmarks[mouth_idx]
                distance = np.linalg.norm(np.array(fingertip_pos) - np.array(mouth_pos))
                if distance < self.NAIL_PULLING_THRESHOLD:
                    return True, mouth_pos
        return False, None

    def check_hair_pulling(self, thumb_pos, finger_pos, forehead_pos):
        """Check if thumb and another finger are close to a forehead landmark"""
        thumb_to_forehead = np.linalg.norm(np.array(thumb_pos) - np.array(forehead_pos))
        if thumb_to_forehead < self.HAIR_PULLING_THRESHOLD:
            finger_to_forehead = np.linalg.norm(np.array(finger_pos) - np.array(forehead_pos))
            finger_to_thumb = np.linalg.norm(np.array(finger_pos) - np.array(thumb_pos))
            
            return (finger_to_forehead < self.HAIR_PULLING_THRESHOLD and 
                   finger_to_thumb < self.HAIR_PULLING_THRESHOLD)
        return False 