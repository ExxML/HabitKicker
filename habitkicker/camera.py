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
        self.show_window = True  # Flag to control window visibility
        self.cap = None
        self.is_calibrating = False
        self.calibration_complete_time = 0  # Track when calibration completed
        self.screen_outline = ScreenOutline()
        
        # Track if calibration was loaded from file
        self.calibration_loaded = self.slouch_detector.calibrated
        self.calibration_loaded_message_time = 0
        
        # Cache for drawing styles to avoid recreating them each frame
        self._face_mesh_tesselation_style = self.mp_handler.mp_drawing_styles.get_default_face_mesh_tesselation_style()
        self._face_mesh_contours_style = self.mp_handler.mp_drawing_styles.get_default_face_mesh_contours_style()
        self._pose_landmarks_style = self.mp_handler.mp_drawing_styles.get_default_pose_landmarks_style()
        
        # Common colors
        self._red = (0, 0, 255)
        self._green = (0, 255, 0)
        self._blue = (255, 0, 0)
        self._yellow = (0, 255, 255)
        self._yellow_alert = (255, 255, 0)
        
        # Window name constant
        self._window_name = 'HabitKicker'

    def _initialize_camera(self):
        """Initialize camera with specific settings"""
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        cap.set(cv2.CAP_PROP_BRIGHTNESS, 150)
        cap.set(cv2.CAP_PROP_CONTRAST, 150)
        return cap
        
    def _toggle_window_visibility(self):
        """Toggle the visibility of the camera window"""
        self.show_window = not self.show_window
        
        if self.show_window:
            # Create window if it doesn't exist
            cv2.namedWindow(self._window_name, cv2.WINDOW_NORMAL)
        else:
            # Destroy window if it exists
            cv2.destroyWindow(self._window_name)
            
        # Print status message
        status = "visible" if self.show_window else "hidden"
        print(f"Camera window is now {status}. Press 'w' to toggle visibility.")

    def calculate_landmark_position(self, landmark, image_shape):
        """Calculate pixel position from normalized landmark coordinates"""
        ih, iw = image_shape[:2]  # Only need height and width
        pixel_x = int(landmark.x * iw)
        pixel_y = int(landmark.y * ih)
        return (pixel_x, pixel_y)

    def _process_face_landmarks(self, frame, face_landmark):
        """Process and draw face landmarks"""
        face_landmarks = {}
        
        # Extract specific landmarks
        landmarks_to_process = self.config.MOUTH_LANDMARKS + self.config.FOREHEAD_LANDMARKS
        
        # Pre-calculate frame shape once
        frame_shape = frame.shape
        
        for idx in landmarks_to_process:
            landmark = face_landmark.landmark[idx]
            pos = self.calculate_landmark_position(landmark, frame_shape)
            face_landmarks[idx] = pos
            
            # Draw landmarks with appropriate colors
            color = self._blue if idx in self.config.MOUTH_LANDMARKS else self._green
            cv2.circle(frame, pos, 5, color, -1)
        
        # Draw face mesh
        self._draw_face_mesh(frame, face_landmark)
        
        return face_landmarks

    def _draw_face_mesh(self, frame, face_landmark):
        """Draw the face mesh and contours"""
        if not self.show_landmarks:
            return
            
        self.mp_handler.mp_drawing.draw_landmarks(
            image = frame,
            landmark_list = face_landmark,
            connections = self.mp_handler.mp_face_mesh.FACEMESH_TESSELATION,
            landmark_drawing_spec = None,
            connection_drawing_spec = self._face_mesh_tesselation_style
        )
        self.mp_handler.mp_drawing.draw_landmarks(
            image = frame,
            landmark_list = face_landmark,
            connections = self.mp_handler.mp_face_mesh.FACEMESH_CONTOURS,
            landmark_drawing_spec = None,
            connection_drawing_spec = self._face_mesh_contours_style
        )

    def _process_hand_landmarks(self, frame, hand_landmarks, face_landmarks):
        """Process hand landmarks and detect habits"""
        nail_biting_detected = False
        hair_pulling_detected = False
        
        # Draw hand landmarks
        if self.show_landmarks:
            self.mp_handler.mp_drawing.draw_landmarks(
                frame, hand_landmarks, self.mp_handler.mp_hands.HAND_CONNECTIONS
            )
        
        # Pre-calculate frame shape once
        frame_shape = frame.shape
        
        # Get thumb position
        thumb_pos = self._get_thumb_position(frame, hand_landmarks, frame_shape)
        
        # Get other fingertip positions
        other_fingertips = self._get_other_fingertip_positions(frame, hand_landmarks, frame_shape)
        
        # Check for nail biting
        nail_biting_detected = self._check_nail_biting(frame, hand_landmarks, face_landmarks, frame_shape)
        
        # Check for hair pulling
        hair_pulling_detected = self._check_hair_pulling(
            frame, thumb_pos, other_fingertips, face_landmarks
        )
        
        return nail_biting_detected, hair_pulling_detected

    def _get_thumb_position(self, frame, hand_landmarks, frame_shape=None):
        """Get and draw thumb position"""
        if frame_shape is None:
            frame_shape = frame.shape
            
        thumb_tip = hand_landmarks.landmark[self.config.THUMB_TIP]
        thumb_pos = self.calculate_landmark_position(thumb_tip, frame_shape)
        if self.show_landmarks:
            cv2.circle(frame, thumb_pos, 8, self._yellow, -1)
        return thumb_pos

    def _get_other_fingertip_positions(self, frame, hand_landmarks, frame_shape=None):
        """Get and draw other fingertip positions"""
        if frame_shape is None:
            frame_shape = frame.shape
            
        positions = {}
        for finger_id in self.config.OTHER_FINGERTIPS:
            fingertip = hand_landmarks.landmark[finger_id]
            pos = self.calculate_landmark_position(fingertip, frame_shape)
            positions[finger_id] = pos
            if self.show_landmarks:
                cv2.circle(frame, pos, 8, self._yellow, -1)
        return positions

    def _check_nail_biting(self, frame, hand_landmarks, face_landmarks, frame_shape=None):
        """Check for nail biting behavior"""
        if frame_shape is None:
            frame_shape = frame.shape
            
        is_biting = False
        for point_id in self.config.FINGERTIP_LANDMARKS:
            fingertip = hand_landmarks.landmark[point_id]
            finger_pos = self.calculate_landmark_position(fingertip, frame_shape)
            
            biting_detected, mouth_pos = self.habit_detector.check_nail_biting(finger_pos, face_landmarks)
            if biting_detected:
                cv2.line(frame, finger_pos, mouth_pos, self._red, 2)
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
        cv2.line(frame, thumb_pos, forehead_pos, self._red, 2)
        cv2.line(frame, finger_pos, forehead_pos, self._red, 2)
        cv2.line(frame, thumb_pos, finger_pos, self._red, 2)

    def _display_alerts(self, frame, nail_biting_detected, hair_pulling_detected, slouching_detected):
        """Display habit detection alerts"""
        if nail_biting_detected:
            cv2.putText(frame, "Nail Biting Detected!", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, self._red, 2)
        
        if hair_pulling_detected:
            cv2.putText(frame, "Hair Pulling Detected!", (50, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, self._red, 2)
        
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
                landmark_drawing_spec = self._pose_landmarks_style
            )
        
        # If calibrating, update calibration
        if self.is_calibrating:
            calibration_complete = self.slouch_detector.update_calibration(frame, pose_landmark)
            if calibration_complete:
                self.is_calibrating = False
                self.calibration_complete_time = time.time()  # Record when calibration completed
        
        # Show "Calibration Complete!" message for 2seconds after calibration
        current_time = time.time()
        if not self.is_calibrating and current_time - self.calibration_complete_time < 2:
            text = "Calibration Complete!"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
            text_height = text_size[1]
            text_x = int((frame.shape[1] - text_size[0]) / 2)
            text_y = int(frame.shape[0] / 2 + text_height / 2)
            
            cv2.putText(frame, text, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, self._green, 2)

        # If not calibrated and not currently calibrating, show a message about posture percentage
        if not self.slouch_detector.calibrated and not self.is_calibrating:
            cv2.putText(frame, "Posture: N/A (Calibration needed)", (50, 130),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, self._yellow, 2)
        
        # Check for slouching
        return self.slouch_detector.check_slouching(frame, pose_landmark)

    def start_calibration(self):
        """Start the slouch detection calibration process"""
        self.is_calibrating = True
        self.slouch_detector.start_calibration()
        
        # Make sure window is visible during calibration
        if not self.show_window:
            self._toggle_window_visibility()

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
            
        # Create initial window
        if self.show_window:
            cv2.namedWindow(self._window_name, cv2.WINDOW_NORMAL)
            
        # Print initial instructions
        print("HabitKicker is running.")
        print("Press 'q' to quit, 'c' to calibrate, 'l' to toggle landmarks")
        print("Press 'w' to toggle window visibility")

        running = True
        
        while running:
            # Get and process frame
            ret, frame = cap.read()
            if not ret:
                break

            try:
                # Convert and process frame with MediaPipe - only convert once
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process all MediaPipe models in parallel
                hands_results = self.mp_handler.hands.process(rgb_frame)
                face_results = self.mp_handler.face_mesh.process(rgb_frame)
                pose_results = self.mp_handler.pose.process(rgb_frame)

                # Process face landmarks
                face_landmarks = {}
                if face_results.multi_face_landmarks:
                    for face_landmark in face_results.multi_face_landmarks:
                        face_landmarks = self._process_face_landmarks(frame, face_landmark)
                        break  # Only process the first face for efficiency

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

                # Cache current time to avoid multiple calls
                current_time = time.time()
                
                # Display calibration instructions if not calibrated
                if not self.slouch_detector.calibrated and not self.is_calibrating:
                    cv2.putText(frame, "Press 'c' to calibrate posture", (50, 210),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, self._yellow_alert, 2)
                
                # Show "Calibration Loaded!" message for 3 seconds after startup if calibration was loaded
                if self.calibration_loaded and current_time - self.calibration_loaded_message_time < 3:
                    text = "Posture Calibration Loaded!"
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                    text_height = text_size[1]
                    text_x = int((frame.shape[1] - text_size[0]) / 2)
                    text_y = int(frame.shape[0] / 2 + text_height / 2)
                    
                    cv2.putText(frame, text, (text_x, text_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, self._green, 2)
                
                # Add window visibility status
                window_status = "Window: Visible (Press 'w' to hide)"
                cv2.putText(frame, window_status, (50, frame.shape[0] - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, self._green, 1)

                # Only display the frame if the window is visible
                if self.show_window:
                    cv2.imshow(self._window_name, frame)
                
                # Always check for key presses, even if window is hidden
                # Use a small wait time to reduce CPU usage when window is hidden
                wait_time = 1 if self.show_window else 100
                key = cv2.waitKey(wait_time) & 0xFF
                
                if key == ord('q'):
                    running = False
                elif key == ord('c'):
                    self.start_calibration()
                elif key == ord('l'):
                    # Toggle landmarks display
                    self.show_landmarks = not self.show_landmarks
                elif key == ord('w'):
                    # Toggle window visibility
                    self._toggle_window_visibility()
                    
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