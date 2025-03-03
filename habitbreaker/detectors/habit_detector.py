"""Class for detecting habits based on landmark positions"""

import numpy as np
from habitbreaker.config.landmark_config import LandmarkConfig

class HabitDetector:
    def __init__(self, habit_threshold=50, finger_threshold=50, slouch_threshold=0.7):
        self.HABIT_THRESHOLD = habit_threshold
        self.FINGER_TO_FINGER_THRESHOLD = finger_threshold
        self.SLOUCH_THRESHOLD = slouch_threshold  # Threshold for slouching detection
        self.config = LandmarkConfig()

    def check_nail_biting(self, fingertip_pos, face_landmarks):
        """Check if a fingertip is close to any mouth landmark"""
        for mouth_idx in self.config.MOUTH_LANDMARKS:
            if mouth_idx in face_landmarks:
                mouth_pos = face_landmarks[mouth_idx]
                distance = np.linalg.norm(np.array(fingertip_pos) - np.array(mouth_pos))
                if distance < self.HABIT_THRESHOLD:
                    return True, mouth_pos
        return False, None

    def check_hair_pulling(self, thumb_pos, finger_pos, forehead_pos):
        """Check if thumb and another finger are close to a forehead landmark"""
        thumb_to_forehead = np.linalg.norm(np.array(thumb_pos) - np.array(forehead_pos))
        if thumb_to_forehead < self.HABIT_THRESHOLD:
            finger_to_forehead = np.linalg.norm(np.array(finger_pos) - np.array(forehead_pos))
            finger_to_thumb = np.linalg.norm(np.array(finger_pos) - np.array(thumb_pos))
            
            return (finger_to_forehead < self.HABIT_THRESHOLD and 
                   finger_to_thumb < self.FINGER_TO_FINGER_THRESHOLD)
        return False

    def check_slouching(self, pose_landmarks):
        """Check if the person is slouching based on upper body landmarks"""
        if not pose_landmarks:
            return False, None

        # Get relevant landmarks
        shoulder_left = np.array([
            pose_landmarks[self.config.SHOULDER_LEFT].x,
            pose_landmarks[self.config.SHOULDER_LEFT].y
        ])
        shoulder_right = np.array([
            pose_landmarks[self.config.SHOULDER_RIGHT].x,
            pose_landmarks[self.config.SHOULDER_RIGHT].y
        ])
        ear_left = np.array([
            pose_landmarks[self.config.EAR_LEFT].x,
            pose_landmarks[self.config.EAR_LEFT].y
        ])
        ear_right = np.array([
            pose_landmarks[self.config.EAR_RIGHT].x,
            pose_landmarks[self.config.EAR_RIGHT].y
        ])
        nose = np.array([
            pose_landmarks[self.config.NOSE].x,
            pose_landmarks[self.config.NOSE].y
        ])
        neck = np.array([
            pose_landmarks[self.config.NECK].x,
            pose_landmarks[self.config.NECK].y
        ])

        # Calculate shoulder line vector
        shoulder_vector = shoulder_right - shoulder_left
        shoulder_angle = np.arctan2(shoulder_vector[1], shoulder_vector[0])

        # Calculate ear line vector
        ear_vector = ear_right - ear_left
        ear_angle = np.arctan2(ear_vector[1], ear_vector[0])

        # Calculate head forward position
        head_forward = nose[0] - neck[0]  # Positive means head is forward
        shoulder_width = np.linalg.norm(shoulder_vector)
        normalized_head_forward = head_forward / shoulder_width

        # Calculate angles
        shoulder_ear_angle = abs(shoulder_angle - ear_angle)
        
        # Check for slouching conditions
        # 1. Head tilted forward (normalized_head_forward > 0.3)
        # 2. Shoulders not level (shoulder_ear_angle > threshold)
        is_slouching = (normalized_head_forward > 0.3 or 
                       shoulder_ear_angle > self.SLOUCH_THRESHOLD)

        # Calculate severity (0-1)
        # Combine both factors: head forward position and shoulder tilt
        severity = min(1.0, (normalized_head_forward + shoulder_ear_angle / np.pi) / 2)

        return is_slouching, severity 