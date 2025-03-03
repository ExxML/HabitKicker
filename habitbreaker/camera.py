"""Main class for camera handling and habit detection"""

import cv2
import numpy as np
from habitbreaker.config.landmark_config import LandmarkConfig
from habitbreaker.detectors.habit_detector import HabitDetector
from habitbreaker.utils.mediapipe_handler import MediapipeHandler

class Camera:
    def __init__(self):
        self.mp_handler = MediapipeHandler()
        self.habit_detector = HabitDetector()
        self.config = LandmarkConfig()
        self.show_landmarks = True
        self.cap = None

    def _initialize_camera(self):
        """Initialize camera with specific settings"""
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        cap.set(cv2.CAP_PROP_BRIGHTNESS, 150)
        cap.set(cv2.CAP_PROP_CONTRAST, 150)
        return cap

    def calculate_landmark_position(self, landmark, image_shape):
        """Calculate pixel position from normalized landmark coordinates"""
        ih, iw, _ = image_shape
        pixel_x = int(landmark.x * iw)
        pixel_y = int(landmark.y * ih)
        return (pixel_x, pixel_y)

    def _process_face_landmarks(self, frame, face_landmark):
        """Process and draw face landmarks"""
        face_landmarks = {}
        
        # Extract specific landmarks
        for idx in self.config.MOUTH_LANDMARKS + self.config.FOREHEAD_LANDMARKS:
            landmark = face_landmark.landmark[idx]
            pos = self.calculate_landmark_position(landmark, frame.shape)
            face_landmarks[idx] = pos
            
            # Draw landmarks with appropriate colors
            color = (255, 0, 0) if idx in self.config.MOUTH_LANDMARKS else (0, 255, 0)
            cv2.circle(frame, pos, 5, color, -1)
        
        # Draw face mesh
        self._draw_face_mesh(frame, face_landmark)
        
        return face_landmarks

    def _draw_face_mesh(self, frame, face_landmark):
        """Draw the face mesh and contours"""
        self.mp_handler.mp_drawing.draw_landmarks(
            image=frame,
            landmark_list=face_landmark,
            connections=self.mp_handler.mp_face_mesh.FACEMESH_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=self.mp_handler.mp_drawing_styles.get_default_face_mesh_tesselation_style()
        )
        self.mp_handler.mp_drawing.draw_landmarks(
            image=frame,
            landmark_list=face_landmark,
            connections=self.mp_handler.mp_face_mesh.FACEMESH_CONTOURS,
            landmark_drawing_spec=None,
            connection_drawing_spec=self.mp_handler.mp_drawing_styles.get_default_face_mesh_contours_style()
        )

    def _process_hand_landmarks(self, frame, hand_landmarks, face_landmarks):
        """Process hand landmarks and detect habits"""
        nail_biting_detected = False
        hair_pulling_detected = False
        
        # Draw hand landmarks
        self.mp_handler.mp_drawing.draw_landmarks(
            frame, hand_landmarks, self.mp_handler.mp_hands.HAND_CONNECTIONS
        )
        
        # Get thumb position
        thumb_pos = self._get_thumb_position(frame, hand_landmarks)
        
        # Get other fingertip positions
        other_fingertips = self._get_other_fingertip_positions(frame, hand_landmarks)
        
        # Check for nail biting
        nail_biting_detected = self._check_nail_biting(frame, hand_landmarks, face_landmarks)
        
        # Check for hair pulling
        hair_pulling_detected = self._check_hair_pulling(
            frame, thumb_pos, other_fingertips, face_landmarks
        )
        
        return nail_biting_detected, hair_pulling_detected

    def _get_thumb_position(self, frame, hand_landmarks):
        """Get and draw thumb position"""
        thumb_tip = hand_landmarks.landmark[self.config.THUMB_TIP]
        thumb_pos = self.calculate_landmark_position(thumb_tip, frame.shape)
        cv2.circle(frame, thumb_pos, 8, (0, 255, 255), -1)
        return thumb_pos

    def _get_other_fingertip_positions(self, frame, hand_landmarks):
        """Get and draw other fingertip positions"""
        positions = {}
        for finger_id in self.config.OTHER_FINGERTIPS:
            fingertip = hand_landmarks.landmark[finger_id]
            pos = self.calculate_landmark_position(fingertip, frame.shape)
            positions[finger_id] = pos
            cv2.circle(frame, pos, 8, (0, 255, 255), -1)
        return positions

    def _check_nail_biting(self, frame, hand_landmarks, face_landmarks):
        """Check for nail biting behavior"""
        for point_id in self.config.FINGERTIP_LANDMARKS:
            fingertip = hand_landmarks.landmark[point_id]
            finger_pos = self.calculate_landmark_position(fingertip, frame.shape)
            
            is_biting, mouth_pos = self.habit_detector.check_nail_biting(finger_pos, face_landmarks)
            if is_biting:
                cv2.line(frame, finger_pos, mouth_pos, (0, 0, 255), 2)
                return True
        return False

    def _check_hair_pulling(self, frame, thumb_pos, other_fingertips, face_landmarks):
        """Check for hair pulling behavior"""
        for forehead_idx in self.config.FOREHEAD_LANDMARKS:
            if forehead_idx in face_landmarks:
                forehead_pos = face_landmarks[forehead_idx]
                
                for finger_pos in other_fingertips.values():
                    if self.habit_detector.check_hair_pulling(thumb_pos, finger_pos, forehead_pos):
                        self._draw_hair_pulling_triangle(frame, thumb_pos, finger_pos, forehead_pos)
                        return True
        return False

    def _draw_hair_pulling_triangle(self, frame, thumb_pos, finger_pos, forehead_pos):
        """Draw triangle for hair pulling visualization"""
        cv2.line(frame, thumb_pos, forehead_pos, (0, 0, 255), 2)
        cv2.line(frame, finger_pos, forehead_pos, (0, 0, 255), 2)
        cv2.line(frame, thumb_pos, finger_pos, (0, 0, 255), 2)

    def _check_slouching(self, frame, pose_landmarks):
        """Check for slouching and draw visualization"""
        if not pose_landmarks:
            return False, 0.0

        is_slouching, severity = self.habit_detector.check_slouching(pose_landmarks)
        
        if is_slouching:
            # Draw slouching visualization
            self._draw_slouching_visualization(frame, pose_landmarks, severity)
            
        return is_slouching, severity

    def _draw_slouching_visualization(self, frame, pose_landmarks, severity):
        """Draw visualization for slouching detection"""
        # Get relevant landmarks
        shoulder_left = self.calculate_landmark_position(
            pose_landmarks[self.config.SHOULDER_LEFT], frame.shape
        )
        shoulder_right = self.calculate_landmark_position(
            pose_landmarks[self.config.SHOULDER_RIGHT], frame.shape
        )
        ear_left = self.calculate_landmark_position(
            pose_landmarks[self.config.EAR_LEFT], frame.shape
        )
        ear_right = self.calculate_landmark_position(
            pose_landmarks[self.config.EAR_RIGHT], frame.shape
        )
        nose = self.calculate_landmark_position(
            pose_landmarks[self.config.NOSE], frame.shape
        )
        neck = self.calculate_landmark_position(
            pose_landmarks[self.config.NECK], frame.shape
        )

        # Draw lines between landmarks
        cv2.line(frame, shoulder_left, shoulder_right, (0, 0, 255), 2)  # Shoulder line
        cv2.line(frame, ear_left, ear_right, (0, 0, 255), 2)  # Ear line
        cv2.line(frame, nose, neck, (0, 0, 255), 2)  # Head forward line

        # Draw severity indicator with color gradient
        severity_color = (
            int(255 * severity),  # Red component
            0,  # Green component
            int(255 * (1 - severity))  # Blue component
        )
        severity_text = f"Slouching Severity: {severity:.2f}"
        cv2.putText(frame, severity_text, (10, 130),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, severity_color, 2)

        # Draw posture guide
        if severity > 0.5:
            cv2.putText(frame, "Sit up straight!", (10, 170),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    def _display_alerts(self, frame, nail_biting_detected, hair_pulling_detected, slouching_detected):
        """Display habit detection alerts"""
        if nail_biting_detected:
            cv2.putText(frame, "Nail Biting Detected!", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        if hair_pulling_detected:
            cv2.putText(frame, "Hair Pulling Detected!", (50, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        if slouching_detected:
            cv2.putText(frame, "Slouching Detected!", (50, 130),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    def start_camera(self):
        """Main method to start camera and process frames"""
        cap = self._initialize_camera()

        while cap.isOpened():
            # Get and process frame
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert and process frame with MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pose_results = self.mp_handler.pose.process(rgb_frame)
            hands_results = self.mp_handler.hands.process(rgb_frame)
            face_results = self.mp_handler.face_mesh.process(rgb_frame)

            # Draw pose landmarks if detected
            if pose_results.pose_landmarks:
                self.mp_handler.mp_drawing.draw_landmarks(
                    frame, pose_results.pose_landmarks, self.mp_handler.mp_pose.POSE_CONNECTIONS
                )

            # Process face landmarks
            face_landmarks = {}
            if face_results.multi_face_landmarks:
                for face_landmark in face_results.multi_face_landmarks:
                    face_landmarks = self._process_face_landmarks(frame, face_landmark)

            # Process hand landmarks and detect habits
            nail_biting = False
            hair_pulling = False
            if hands_results.multi_hand_landmarks and face_landmarks:
                for hand_landmarks in hands_results.multi_hand_landmarks:
                    nail_biting, hair_pulling = self._process_hand_landmarks(
                        frame, hand_landmarks, face_landmarks
                    )

            # Check for slouching
            slouching = False
            if pose_results.pose_landmarks:
                slouching, _ = self._check_slouching(frame, pose_results.pose_landmarks.landmark)

            # Display all alerts
            self._display_alerts(frame, nail_biting, hair_pulling, slouching)

            # Display output and check for exit
            cv2.imshow('HabitBreaker', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Cleanup
        cap.release()
        cv2.destroyAllWindows() 