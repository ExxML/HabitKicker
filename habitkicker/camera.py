"""Main class for camera handling and habit detection"""

import cv2
import time
from habitkicker.config.landmark_config import LandmarkConfig
from habitkicker.detectors.habit_detector import HabitDetector
from habitkicker.detectors.slouch_detector import SlouchDetector
from habitkicker.utils.mediapipe_handler import MediapipeHandler
from habitkicker.utils.screen_overlay import ScreenOutline

class Camera:
    def __init__(self, nail_biting_threshold = 40, hair_pulling_threshold = 50, slouch_threshold = 15):
        self.mp_handler = MediapipeHandler()
        self.habit_detector = HabitDetector(nail_biting_threshold, hair_pulling_threshold)
        self.slouch_detector = SlouchDetector(threshold_percentage = slouch_threshold)
        self.config = LandmarkConfig()
        self.show_landmarks = True
        self.cap = None
        self.is_calibrating = False
        self.calibration_complete_time = 0  # Track when calibration completed
        self.screen_outline = ScreenOutline()
        
        # Track if calibration was loaded from file
        self.calibration_loaded = self.slouch_detector.calibrated
        self.calibration_loaded_message_time = 0

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
            image = frame,
            landmark_list = face_landmark,
            connections = self.mp_handler.mp_face_mesh.FACEMESH_TESSELATION,
            landmark_drawing_spec = None,
            connection_drawing_spec = self.mp_handler.mp_drawing_styles.get_default_face_mesh_tesselation_style()
        )
        self.mp_handler.mp_drawing.draw_landmarks(
            image = frame,
            landmark_list = face_landmark,
            connections = self.mp_handler.mp_face_mesh.FACEMESH_CONTOURS,
            landmark_drawing_spec = None,
            connection_drawing_spec = self.mp_handler.mp_drawing_styles.get_default_face_mesh_contours_style()
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
        is_biting = False
        for point_id in self.config.FINGERTIP_LANDMARKS:
            fingertip = hand_landmarks.landmark[point_id]
            finger_pos = self.calculate_landmark_position(fingertip, frame.shape)
            
            biting_detected, mouth_pos = self.habit_detector.check_nail_biting(finger_pos, face_landmarks)
            if biting_detected:
                cv2.line(frame, finger_pos, mouth_pos, (0, 0, 255), 2)
                is_biting = True
        return is_biting

    def _check_hair_pulling(self, frame, thumb_pos, other_fingertips, face_landmarks):
        """Check for hair pulling behavior"""
        is_pulling = False
        for forehead_idx in self.config.FOREHEAD_LANDMARKS:
            if forehead_idx in face_landmarks:
                forehead_pos = face_landmarks[forehead_idx]
                
                for finger_pos in other_fingertips.values():
                    if self.habit_detector.check_hair_pulling(thumb_pos, finger_pos, forehead_pos):
                        self._draw_hair_pulling_triangle(frame, thumb_pos, finger_pos, forehead_pos)
                        is_pulling = True
        return is_pulling

    def _draw_hair_pulling_triangle(self, frame, thumb_pos, finger_pos, forehead_pos):
        """Draw triangle for hair pulling visualization"""
        cv2.line(frame, thumb_pos, forehead_pos, (0, 0, 255), 2)
        cv2.line(frame, finger_pos, forehead_pos, (0, 0, 255), 2)
        cv2.line(frame, thumb_pos, finger_pos, (0, 0, 255), 2)

    def _display_alerts(self, frame, nail_biting_detected, hair_pulling_detected, slouching_detected):
        """Display habit detection alerts"""
        if nail_biting_detected:
            cv2.putText(frame, "Nail Biting Detected!", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        if hair_pulling_detected:
            cv2.putText(frame, "Hair Pulling Detected!", (50, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Slouching alert is handled by the slouch detector itself
        
        # Update screen outline with habit status
        self.screen_outline.update_habit_status(
            nail_biting_detected, 
            hair_pulling_detected, 
            slouching_detected
        )

    def _process_pose_landmarks(self, frame, pose_landmark):
        """Process and draw pose landmarks for slouch detection"""
        if self.show_landmarks:
            # Draw pose landmarks
            self.mp_handler.mp_drawing.draw_landmarks(
                frame,
                pose_landmark,
                self.mp_handler.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec = self.mp_handler.mp_drawing_styles.get_default_pose_landmarks_style()
            )
        
        # If calibrating, update calibration
        if self.is_calibrating:
            calibration_complete = self.slouch_detector.update_calibration(frame, pose_landmark)
            if calibration_complete:
                self.is_calibrating = False
                self.calibration_complete_time = time.time()  # Record when calibration completed
        
        # Show "Calibration Complete!" message for 2seconds after calibration
        if not self.is_calibrating and time.time() - self.calibration_complete_time < 2:
            text = "Calibration Complete!"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
            text_x = int((frame.shape[1] - text_size[0]) / 2)
            text_y = int(frame.shape[0] / 2)
            
            cv2.putText(frame, text, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
        
        # If not calibrated and not currently calibrating, show a message about posture percentage
        if not self.slouch_detector.calibrated and not self.is_calibrating:
            cv2.putText(frame, "Posture: N/A (Calibration needed)", (50, 130),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        # Check for slouching
        return self.slouch_detector.check_slouching(frame, pose_landmark)

    def start_calibration(self):
        """Start the slouch detection calibration process"""
        self.is_calibrating = True
        self.slouch_detector.start_calibration()

    def start_camera(self):
        """Main method to start camera and process frames"""
        cap = self._initialize_camera()
        self.cap = cap
        
        # Set time for showing calibration loaded message
        if self.calibration_loaded:
            self.calibration_loaded_message_time = time.time()

        # Start with calibration if not already calibrated
        if not self.slouch_detector.calibrated:
            self.start_calibration()

        running = True
        while running:
            # Get and process frame
            ret, frame = cap.read()
            if not ret:
                break

            try:
                # Convert and process frame with MediaPipe
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                hands_results = self.mp_handler.hands.process(rgb_frame)
                face_results = self.mp_handler.face_mesh.process(rgb_frame)
                pose_results = self.mp_handler.pose.process(rgb_frame)

                # Process face landmarks
                face_landmarks = {}
                if face_results.multi_face_landmarks:
                    for face_landmark in face_results.multi_face_landmarks:
                        face_landmarks = self._process_face_landmarks(frame, face_landmark)

                # Process pose landmarks for slouch detection
                slouching_detected = False
                if pose_results.pose_landmarks:
                    slouching_detected = self._process_pose_landmarks(frame, pose_results.pose_landmarks)

                # Process hand landmarks and detect habits
                nail_biting = False
                hair_pulling = False
                
                if hands_results.multi_hand_landmarks and face_landmarks:
                    for hand_landmarks in hands_results.multi_hand_landmarks:
                        # Process each hand and combine the results
                        hand_nail_biting, hand_hair_pulling = self._process_hand_landmarks(
                            frame, hand_landmarks, face_landmarks
                        )
                        # If either hand is doing the habit, mark it as detected
                        nail_biting = nail_biting or hand_nail_biting
                        hair_pulling = hair_pulling or hand_hair_pulling

                # Display alerts
                self._display_alerts(frame, nail_biting, hair_pulling, slouching_detected)

                # Display calibration instructions if not calibrated
                if not self.slouch_detector.calibrated and not self.is_calibrating:
                    cv2.putText(frame, "Press 'c' to calibrate posture", (50, 210),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                
                # Show "Calibration Loaded!" message for 3 seconds after startup if calibration was loaded
                if self.calibration_loaded and time.time() - self.calibration_loaded_message_time < 3:
                    text = "Posture Calibration Loaded!"
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
                    text_x = int((frame.shape[1] - text_size[0]) / 2)
                    text_y = int(frame.shape[0] / 2) + 80
                    
                    cv2.putText(frame, text, (text_x, text_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

                # Display output and check for exit or calibration
                cv2.imshow('HabitKicker', frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    running = False
                elif key == ord('c'):
                    self.start_calibration()
            except Exception as e:
                print(f"Error processing frame: {e}")
                time.sleep(0.5)  # Wait a bit before retrying

        # Cleanup
        try:
            # First release OpenCV resources
            cap.release()
            cv2.destroyAllWindows()
        except Exception as e:
            print(f"Warning during OpenCV cleanup: {e}")

        # Then cleanup screen outline (don't wait for it)
        try:
            self.screen_outline.cleanup()
        except Exception as e:
            print(f"Warning during screen outline cleanup: {e}") 