"""Class for detecting slouching based on posture landmarks"""

import numpy as np
import cv2
import time
import os
import pickle
from pathlib import Path

class SlouchDetector:
    def __init__(self, threshold_percentage):
        self.calibrated = False
        self.calibration_landmarks = None
        self.threshold_percentage = threshold_percentage
        self.calibration_countdown = 0
        self.calibration_start_time = 0
        self.calibration_duration = 3.0  # seconds
        
        # New variables for collecting posture data during calibration
        self.calibration_samples = []
        self.last_sample_time = 0
        self.sample_interval = 0.1  # Collect samples every 100 ms
        
        # Path for saving calibration data
        # Get the project root directory (assuming we're in habitkicker/detectors)
        project_root = Path(__file__).parent.parent.parent
        self.calibration_dir = project_root / "data"
        self.calibration_file = self.calibration_dir / "posture_calibration.pkl"
        
        # Try to load existing calibration data
        self.load_calibration()
        
    def start_calibration(self):
        """Start the calibration process"""
        self.calibrated = False
        self.calibration_landmarks = None
        self.calibration_countdown = 3  # 3 second countdown before calibration
        self.calibration_start_time = time.time()
        self.calibration_samples = []  # Reset samples
        
    def update_calibration(self, frame, pose_landmarks):
        """Update calibration process and draw UI elements"""
        current_time = time.time()
        
        # Handle countdown phase
        if self.calibration_countdown > 0:
            elapsed = current_time - self.calibration_start_time
            remaining = self.calibration_countdown - elapsed
            
            if remaining <= 0:
                # Countdown finished, start actual calibration
                self.calibration_countdown = 0
                self.calibration_start_time = current_time
                self.calibration_samples = []  # Reset samples
                self.last_sample_time = current_time
                return False
            
            # Draw countdown
            self._draw_calibration_countdown(frame, remaining)
            return False
            
        # Handle actual calibration phase
        elapsed = current_time - self.calibration_start_time
        if elapsed < self.calibration_duration:
            # Still calibrating
            progress = int((elapsed / self.calibration_duration) * 100)
            
            # Collect samples at regular intervals
            if current_time - self.last_sample_time >= self.sample_interval and pose_landmarks:
                self.last_sample_time = current_time
                landmarks = self._extract_posture_landmarks(pose_landmarks)
                if landmarks:
                    self.calibration_samples.append(landmarks)
                    # Update the progress text to show samples collected
                    self._draw_calibration_progress(frame, progress, len(self.calibration_samples))
                else:
                    self._draw_calibration_progress(frame, progress, len(self.calibration_samples))
            else:
                self._draw_calibration_progress(frame, progress, len(self.calibration_samples))
                
            return False
        else:
            # Calibration complete
            if not self.calibrated and len(self.calibration_samples) > 0:
                self._complete_calibration()
            return True
    
    def _complete_calibration(self):
        """Complete the calibration process by averaging collected landmarks"""
        if len(self.calibration_samples) == 0:
            print("Warning: No calibration samples collected")
            return
            
        # Average all collected samples
        avg_landmarks = {}
        
        # Initialize with the structure of the first sample
        for key in self.calibration_samples[0].keys():
            # Each landmark has 3 coordinates (x, y, z)
            avg_landmarks[key] = [0, 0, 0]
        
        # Sum all samples
        for sample in self.calibration_samples:
            for key, coords in sample.items():
                for i in range(3):  # x, y, z
                    avg_landmarks[key][i] += coords[i]
        
        # Divide by number of samples to get average
        for key in avg_landmarks.keys():
            for i in range(3):  # x, y, z
                avg_landmarks[key][i] /= len(self.calibration_samples)
            
            # Convert lists back to tuples
            avg_landmarks[key] = tuple(avg_landmarks[key])
        
        # Store the averaged landmarks
        self.calibration_landmarks = avg_landmarks
        self.calibrated = True
        print(f"Calibration complete with {len(self.calibration_samples)} samples")
        
        # Save the calibration data
        self.save_calibration()
    
    def _draw_calibration_countdown(self, frame, remaining):
        """Draw countdown UI during calibration preparation"""
        h, w, _ = frame.shape
        
        text = f"Sit up straight! Calibration in {int(remaining)+1}..."
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
        text_x = int((w - text_size[0]) / 2)
        text_y = int(h / 2)
        
        cv2.putText(
            frame, 
            text, 
            (text_x, text_y), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (0, 255,0), 
            2
        )
    
    def _draw_calibration_progress(self, frame, progress, samples_count=0):
        """Draw progress bar during calibration"""
        h, w, _ = frame.shape
        
        # Draw text
        text = "Calibrating posture... Stay still and sit up straight"
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        text_x = int((w - text_size[0]) / 2)
        text_y = int(h / 2) - 30
        
        cv2.putText(
            frame, 
            text, 
            (text_x, text_y), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.8, 
            (0, 255, 0), 
            2
        )
        
        # Draw progress bar
        bar_width = 400
        bar_height = 30
        bar_x = int(w/2) - int(bar_width/2)
        bar_y = int(h/2) + 20
        
        # Background
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (100, 100, 100), -1)
        
        # Progress
        progress_width = int((progress / 100) * bar_width)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), (0, 255, 0), -1)
        
        # Border
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 2)
    
    def _extract_posture_landmarks(self, pose_landmarks):
        """Extract relevant landmarks for posture analysis"""
        # We're only interested in upper body landmarks (shoulders, neck, nose)
        landmarks = {}
        
        if hasattr(pose_landmarks, 'landmark'):
            # Extract shoulder landmarks (11 and 12 in MediaPipe Pose)
            landmarks['left_shoulder'] = (
                pose_landmarks.landmark[11].x,
                pose_landmarks.landmark[11].y,
                pose_landmarks.landmark[11].z
            )
            landmarks['right_shoulder'] = (
                pose_landmarks.landmark[12].x,
                pose_landmarks.landmark[12].y,
                pose_landmarks.landmark[12].z
            )
            
            # Extract neck landmark (mid-point between shoulders)
            landmarks['neck'] = (
                (pose_landmarks.landmark[11].x + pose_landmarks.landmark[12].x) / 2,
                (pose_landmarks.landmark[11].y + pose_landmarks.landmark[12].y) / 2,
                (pose_landmarks.landmark[11].z + pose_landmarks.landmark[12].z) / 2
            )
            
            # Nose landmark for vertical alignment
            landmarks['nose'] = (
                pose_landmarks.landmark[0].x,
                pose_landmarks.landmark[0].y,
                pose_landmarks.landmark[0].z
            )
            
            # Add ear landmarks for head tilt detection
            landmarks['left_ear'] = (
                pose_landmarks.landmark[7].x,
                pose_landmarks.landmark[7].y,
                pose_landmarks.landmark[7].z
            )
            landmarks['right_ear'] = (
                pose_landmarks.landmark[8].x,
                pose_landmarks.landmark[8].y,
                pose_landmarks.landmark[8].z
            )
            
        return landmarks
    
    def check_slouching(self, frame, pose_landmarks):
        """Check if the user is slouching based on calibrated posture"""
        if not self.calibrated or not pose_landmarks:
            return False
        
        current_landmarks = self._extract_posture_landmarks(pose_landmarks)
        
        # If we couldn't extract the necessary landmarks, return False
        if not current_landmarks or not self.calibration_landmarks:
            return False
        
        # Calculate slouch metrics
        slouch_detected, slouch_percentage = self._calculate_slouch(current_landmarks)
        
        # Always draw the slouch percentage
        if slouch_detected:
            self._draw_slouch_alert(frame, slouch_percentage)
        else:
            self._draw_slouch_percentage(frame, slouch_percentage)
            
        return slouch_detected
    
    def _calculate_slouch(self, current_landmarks):
        """Calculate if the user is slouching and by how much"""
        # Calculate multiple slouch indicators
        
        # 1. Vertical change in shoulder position
        left_shoulder_y_diff = current_landmarks['left_shoulder'][1] - self.calibration_landmarks['left_shoulder'][1]
        right_shoulder_y_diff = current_landmarks['right_shoulder'][1] - self.calibration_landmarks['right_shoulder'][1]
        avg_shoulder_diff = (left_shoulder_y_diff + right_shoulder_y_diff) / 2
        
        # 2. Change in neck-to-nose angle
        # Calculate the angle between the neck-nose line in calibration vs current
        cal_neck_nose_vector = np.array([
            self.calibration_landmarks['nose'][0] - self.calibration_landmarks['neck'][0],
            self.calibration_landmarks['nose'][1] - self.calibration_landmarks['neck'][1]
        ])
        curr_neck_nose_vector = np.array([
            current_landmarks['nose'][0] - current_landmarks['neck'][0],
            current_landmarks['nose'][1] - current_landmarks['neck'][1]
        ])
        
        # Normalize vectors
        cal_neck_nose_norm = np.linalg.norm(cal_neck_nose_vector)
        curr_neck_nose_norm = np.linalg.norm(curr_neck_nose_vector)
        
        if cal_neck_nose_norm > 0 and curr_neck_nose_norm > 0:
            cal_neck_nose_vector = cal_neck_nose_vector / cal_neck_nose_norm
            curr_neck_nose_vector = curr_neck_nose_vector / curr_neck_nose_norm
            
            # Calculate dot product and angle
            dot_product = np.clip(np.dot(cal_neck_nose_vector, curr_neck_nose_vector), -1.0, 1.0)
            angle_diff = np.arccos(dot_product) * (180 / np.pi)  # Convert to degrees
        else:
            angle_diff = 0
        
        # 3. Calculate distance between nose and neck (shorter when slouching)
        cal_nose_neck_dist = np.linalg.norm(np.array([
            self.calibration_landmarks['nose'][0] - self.calibration_landmarks['neck'][0],
            self.calibration_landmarks['nose'][1] - self.calibration_landmarks['neck'][1]
        ]))
        
        curr_nose_neck_dist = np.linalg.norm(np.array([
            current_landmarks['nose'][0] - current_landmarks['neck'][0],
            current_landmarks['nose'][1] - current_landmarks['neck'][1]
        ]))
        
        # Calculate distance ratio (less than 1 means slouching)
        dist_ratio = curr_nose_neck_dist / cal_nose_neck_dist if cal_nose_neck_dist > 0 else 1
        
        # Combine metrics to calculate slouch percentage
        # Weight the metrics: shoulder position (60%), angle change (30%), distance ratio (10%)
        shoulder_factor = 0.6
        angle_factor = 0.3
        distance_factor = 0.1
        
        # Calculate reference distance for shoulder movement percentage
        ref_distance = abs(self.calibration_landmarks['nose'][1] - 
                          (self.calibration_landmarks['left_shoulder'][1] + 
                           self.calibration_landmarks['right_shoulder'][1]) / 2)
        
        shoulder_percentage = (avg_shoulder_diff / ref_distance) * 100 if ref_distance > 0 else 0
        angle_percentage = angle_diff * 2  # Scale angle difference to percentage
        distance_percentage = (1 - dist_ratio) * 100 if dist_ratio < 1 else 0
        
        # Combine metrics
        slouch_percentage = (
            shoulder_percentage * shoulder_factor + # Shoulder detection
            angle_percentage * angle_factor + # Neck angle detection
            distance_percentage * distance_factor # Nose-neck distance detection
        )
        
        # Detect slouching if the percentage exceeds the threshold
        slouch_detected = slouch_percentage > self.threshold_percentage
        
        return slouch_detected, slouch_percentage
    
    def _draw_slouch_alert(self, frame, slouch_percentage):
        """Draw slouch alert on the frame"""
        h, w, _ = frame.shape
        
        # Draw alert text
        cv2.putText(
            frame, 
            f"Slouching: {int(slouch_percentage)}% (Threshold: {self.threshold_percentage}%)", 
            (50, 130), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.8, 
            (0, 0, 255), 
            2
        )
        
        # Draw posture correction instruction
        cv2.putText(
            frame, 
            "Please sit up straight", 
            (50, 170), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.8, 
            (0, 0, 255), 
            2
        )
    
    def _draw_slouch_percentage(self, frame, slouch_percentage):
        """Draw slouch percentage on the frame when not slouching"""
        # Calculate color based on how close to threshold (green to yellow)
        ratio = min(slouch_percentage / self.threshold_percentage, 0.9)  # Cap at 90% of threshold
        # Green (0,255,0) to Yellow (0,255,255)
        color = (0, 255, int(255 * ratio))
        
        # Draw percentage text
        cv2.putText(
            frame, 
            f"Posture: {int(slouch_percentage)}% (Threshold: {self.threshold_percentage}%)", 
            (50, 130), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.8, 
            color, 
            2
        )
    
    def save_calibration(self):
        """Save calibration data to a file"""
        if not self.calibrated or self.calibration_landmarks is None:
            print("No calibration data to save")
            return False
            
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.calibration_dir, exist_ok=True)
            
            # Save calibration data
            with open(self.calibration_file, 'wb') as f:
                pickle.dump(self.calibration_landmarks, f)
                
            print(f"Calibration data saved to {self.calibration_file}")
            return True
        except Exception as e:
            print(f"Error saving calibration data: {e}")
            return False
    
    def load_calibration(self):
        """Load calibration data from a file"""
        if not self.calibration_file.exists():
            print("No calibration file found")
            return False
            
        try:
            with open(self.calibration_file, 'rb') as f:
                self.calibration_landmarks = pickle.load(f)
                
            if self.calibration_landmarks:
                self.calibrated = True
                print(f"Calibration data loaded from {self.calibration_file}")
                return True
            else:
                print("Calibration file exists but contains no data")
                return False
        except Exception as e:
            print(f"Error loading calibration data: {e}")
            return False 