"""Module for creating screen overlays and outlines"""

import time
import threading
import tkinter as tk
from tkinter import Toplevel, Canvas
import pygame.mixer
import os

class ScreenOutline:
    def __init__(self, thickness = 10, alpha = 1):
        """Initialize the screen outline overlay
        
        Args:
            thickness: Thickness of the outline in pixels
            alpha: Transparency of the outline (0-1, where 1 is opaque)
        """
        self.thickness = thickness
        self.alpha = alpha
        self.root = None
        self.windows = []
        self.current_color = None
        self.is_showing = False
        self.shutdown_requested = False
        self.habit_status = {
            'nail_biting': {'active': False, 'start_time': 0},
            'hair_pulling': {'active': False, 'start_time': 0},
            'slouching': {'active': False, 'start_time': 0}
        }
        self.detection_threshold = 3.0  # seconds
        self.clear_threshold = 2.0  # seconds
        self.last_detection_time = 0
        self.message_text = ""
        
        # Alert escalation tracking
        self.orange_outline_start_time = 0  # When orange outline first appeared
        self.red_outline_start_time = 0     # When red outline first appeared
        self.escalation_threshold = 3.0     # Time before escalating to next alert level
        self.tint_window = None
        self.is_tinted = False
        
        # Green feedback tracking
        self.green_feedback_active = False  # Whether green feedback is active
        self.green_start_time = 0           # When green outline was shown
        self.green_duration = 1.0           # How long to show green outline (seconds)
        
        # Notification window
        self.notification_window = None
        self.notification_visible = False
        
        # Audio alert tracking
        self.audio_playing = False
        self.audio_initialized = False
        self.beep_sound = None
        self.tint_start_time = 0  # When the red tint was first shown
        self.alarm_volume = 0.1  # Volume for the alarm sound
        
        # Initialize tkinter in a separate thread
        self.init_thread = threading.Thread(target = self._init_tkinter)
        self.init_thread.daemon = True
        self.init_thread.start()
    
    def _init_tkinter(self):
        """Initialize tkinter root window and setup screen outline windows"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Create outline windows (top, right, bottom, left)
        self._create_outline_windows(screen_width, screen_height)
        
        # Initialize audio
        sound_path = os.path.join("sounds", "beep.wav")
        if os.path.exists(sound_path):
            self.initialize_audio(sound_path)
        else:
            print(f"Warning: Sound file not found at {sound_path}")
        
        # Check for shutdown periodically
        self.root.after(100, self._check_shutdown)
        
        # Start the tkinter main loop
        self.root.mainloop()
    
    def _create_outline_windows(self, width, height):
        """Create the four windows that form the screen outline
        
        Args:
            width: Screen width
            height: Screen height
        """
        # Clear any existing windows
        for window in self.windows:
            window.destroy()
        self.windows = []
        
        # Create the four outline segments
        # Top
        top = self._create_outline_segment(0, 0, width, self.thickness)
        self.windows.append(top)
        
        # Right
        right = self._create_outline_segment(width - self.thickness, 0, self.thickness, height)
        self.windows.append(right)
        
        # Bottom
        bottom = self._create_outline_segment(0, height - self.thickness, width, self.thickness)
        self.windows.append(bottom)
        
        # Left
        left = self._create_outline_segment(0, 0, self.thickness, height)
        self.windows.append(left)
        
        # Create message window in top-left corner
        msg_window = self._create_message_window(self.thickness + 10, 10, 400, 100)
        self.windows.append(msg_window)
        
        # Create notification window in top-left corner
        self._create_notification_window(11, 11, 260, 122)
        
        # Create tint window (initially hidden)
        self._create_tint_window(width, height)
        
        # Hide all windows initially
        self.hide_outline()
    
    def _create_outline_segment(self, x, y, width, height):
        """Create a single outline segment window
        
        Args:
            x, y: Position coordinates
            width, height: Dimensions of the segment
        
        Returns:
            Toplevel window object
        """
        window = Toplevel(self.root)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.overrideredirect(True)  # Remove window decorations
        window.attributes("-topmost", True)  # Keep on top
        window.attributes("-alpha", self.alpha)  # Set transparency
        
        # Make window click-through
        window.attributes("-transparentcolor", "black")
        
        # Create canvas for drawing
        canvas = Canvas(window, bg = "black", highlightthickness = 0, width = width, height = height)
        canvas.pack(fill = tk.BOTH, expand = True)
        
        return window
    
    def _create_message_window(self, x, y, width, height):
        """Create a window for displaying detection messages
        
        Args:
            x, y: Position coordinates
            width, height: Dimensions of the window
        
        Returns:
            Toplevel window object
        """
        window = Toplevel(self.root)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.overrideredirect(True)  # Remove window decorations
        window.attributes("-topmost", True)  # Keep on top
        window.attributes("-alpha", self.alpha)  # Set transparency
        
        # Make window click-through
        window.attributes("-transparentcolor", "black")
        
        # Create canvas for drawing text
        canvas = Canvas(window, bg = "black", highlightthickness = 0, width = width, height = height)
        canvas.pack(fill = tk.BOTH, expand = True)

        # Add text item
        canvas.create_text(10, 20, anchor = "nw", text = "", fill = "red", font = ("Calibri", 18), tags = "message")
        
        return window
    
    def _create_notification_window(self, x, y, width, height):
        """Create a notification window in the top-left corner
        
        Args:
            x, y: Position coordinates
            width, height: Dimensions of the window
        """
        window = Toplevel(self.root)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.overrideredirect(True)  # Remove window decorations
        window.attributes("-topmost", True)  # Keep on top
        window.attributes("-alpha", 0.9)  # Set transparency
        
        # Create canvas for drawing
        canvas = Canvas(window, highlightthickness = 0, width = width, height = height)
        canvas.pack(fill = tk.BOTH, expand = True)
        
        # Create notification background
        canvas.create_rectangle(0, 0, width, height, fill = "black", outline = "gray", width = 2, tags = "bg")
        
        # Add title
        canvas.create_text(10, 10, anchor = "nw", text = "HabitKicker Alert", fill = "white", 
                          font = ("Calibri", 15, "bold"), tags = "title")
        
        # Add horizontal line
        canvas.create_line(10, 35, width - 10, 35, fill = "gray", tags = "line")
        
        # Add message text
        canvas.create_text(10, 45, anchor = "nw", text = "", fill = "white", 
                          font = ("Calibri", 13), width = width - 20, tags = "notification_text")
        
        # Hide the window initially
        window.withdraw()
        
        self.notification_window = window
        return window
    
    def _create_tint_window(self, width, height):
        """Create a semi-transparent window that covers the entire screen for tinting
        
        Args:
            width: Screen width
            height: Screen height
        """
        window = Toplevel(self.root)
        window.geometry(f"{width}x{height}+0+0")
        window.overrideredirect(True)  # Remove window decorations
        window.attributes("-topmost", True)  # Keep on top
        window.attributes("-alpha", 0.2)  # Set transparency to 20%
        
        # Make window click-through
        window.attributes("-transparentcolor", "black")
        
        # Create canvas for drawing
        canvas = Canvas(window, bg = "black", highlightthickness = 0, width = width, height = height)
        canvas.pack(fill = tk.BOTH, expand = True)
        
        # Hide the window initially
        window.withdraw()
        
        self.tint_window = window
    
    def show_outline(self, color):
        """Show the outline with the specified color
        
        Args:
            color: Color name ("orange", "red", etc.)
        """
        if not self.root or not self.windows:
            return
            
        # If color is changing, update the start time for the new color
        if self.current_color != color:
            current_time = time.time()
            if color == "orange":
                self.orange_outline_start_time = current_time
            elif color == "red":
                self.red_outline_start_time = current_time
        
        self.current_color = color
        
        # Update all outline windows
        for window in self.windows[:-1]:  # Skip message window
            canvas = window.winfo_children()[0]
            canvas.configure(bg = color)
        
        # Show all windows
        for window in self.windows:
            window.deiconify()
            
        # Update notification color to match outline
        self._update_notification_color(color)
        
        self.is_showing = True
    
    def hide_outline(self):
        """Hide the outline"""
        if not self.root or not self.windows:
            return
            
        # Hide all outline windows (but not the tint window)
        for window in self.windows:
            window.withdraw()
        
        # Hide notification window
        if self.notification_window:
            self.notification_window.withdraw()
            self.notification_visible = False
        
        self.is_showing = False
    
    def update_message(self, message):
        """Update the detection message
        
        Args:
            message: Text message to display
        """
        if not self.root or len(self.windows) < 5:
            return
            
        # Get message window and its canvas
        msg_window = self.windows[-1]
        canvas = msg_window.winfo_children()[0]
        
        # Always set empty string to hide messages in screen overlay
        canvas.itemconfig("message", text = "")
        
        # Update notification text - still show messages in notification
        self._update_notification_text(message)
    
    def _update_notification_text(self, message):
        """Update the notification window text
        
        Args:
            message: Text message to display
        """
        if not self.root or not self.notification_window:
            return
            
        canvas = self.notification_window.winfo_children()[0]
        
        # Update text
        canvas.itemconfig("notification_text", text = message)
        
        # Show or hide notification based on message content and current color
        # Don't show notification for green outline
        if message and not self.notification_visible and self.is_showing and self.current_color != "green2":
            self.notification_window.deiconify()
            self.notification_visible = True
        elif (not message and self.notification_visible) or (self.current_color == "green2" and self.notification_visible):
            self.notification_window.withdraw()
            self.notification_visible = False
    
    def update_habit_status(self, nail_biting, hair_pulling, slouching):
        """Update the habit detection status and manage outline display
        
        Args:
            nail_biting: Whether nail biting is detected
            hair_pulling: Whether hair pulling is detected
            slouching: Whether slouching is detected
        """
        current_time = time.time()
        any_habit_active = False
        any_habit_detected = False  # Track if any habit is currently detected (even if not for 3 seconds yet)
        messages = []
        immediate_messages = []  # For habits that should show messages immediately
        
        # First, check if green feedback is active and should be ended
        if self.green_feedback_active:
            if current_time - self.green_start_time >= self.green_duration:
                # Green feedback duration is over, hide the outline
                self.hide_outline()
                self.green_feedback_active = False
                # Clear the message
                self.message_text = ""
                self.update_message(self.message_text)
                
            # While green feedback is active, don't process other habit updates
            return
        
        # Update nail biting status
        if nail_biting:
            any_habit_detected = True
            if not self.habit_status['nail_biting']['active']:
                self.habit_status['nail_biting']['start_time'] = current_time
                self.habit_status['nail_biting']['active'] = True
            
            # Check if this habit was previously detected for 3+ seconds
            if current_time - self.habit_status['nail_biting']['start_time'] >= self.detection_threshold:
                any_habit_active = True
                messages.append("Nail Biting Detected!")
            # If outline is already showing, display message immediately
            elif self.is_showing:
                immediate_messages.append("Nail Biting Detected!")
        else:
            self.habit_status['nail_biting']['active'] = False
        
        # Update hair pulling status
        if hair_pulling:
            any_habit_detected = True
            if not self.habit_status['hair_pulling']['active']:
                self.habit_status['hair_pulling']['start_time'] = current_time
                self.habit_status['hair_pulling']['active'] = True
            
            # Check if this habit was previously detected for 3+ seconds
            if current_time - self.habit_status['hair_pulling']['start_time'] >= self.detection_threshold:
                any_habit_active = True
                messages.append("Hair Pulling Detected!")
            # If outline is already showing, display message immediately
            elif self.is_showing:
                immediate_messages.append("Hair Pulling Detected!")
        else:
            self.habit_status['hair_pulling']['active'] = False
        
        # Update slouching status
        if slouching:
            any_habit_detected = True
            if not self.habit_status['slouching']['active']:
                self.habit_status['slouching']['start_time'] = current_time
                self.habit_status['slouching']['active'] = True
            
            # Check if this habit was previously detected for 3+ seconds
            if current_time - self.habit_status['slouching']['start_time'] >= self.detection_threshold:
                any_habit_active = True
                messages.append("Slouching Detected!")
            # If outline is already showing, display message immediately
            elif self.is_showing:
                immediate_messages.append("Slouching Detected!")
        else:
            self.habit_status['slouching']['active'] = False
        
        # Manage outline display and messages
        if any_habit_active:
            # Update the last detection time when a habit is active for 3+ seconds
            self.last_detection_time = current_time
            
            # Determine which alert level to show based on escalation timing
            if self.is_showing and self.current_color == "red" and self.is_tinted == False:
                # Check if red outline has been showing long enough to add tint
                if current_time - self.red_outline_start_time >= self.escalation_threshold:
                    self.show_tint()
            elif self.is_showing and self.current_color == "orange":
                # Check if orange outline has been showing long enough to turn red
                if current_time - self.orange_outline_start_time >= self.escalation_threshold:
                    self.show_outline("red")
            elif not self.is_showing:
                # Initial detection - show orange outline
                self.show_outline("orange")
            
            # Update message
            self.message_text = "\n".join(messages)
            self.update_message(self.message_text)
        else:
            # If outline is showing and we have immediate messages, display them
            if self.is_showing and immediate_messages:
                self.message_text = "\n".join(immediate_messages)
                self.update_message(self.message_text)
            # Otherwise, clear message if no habits are active for 3+ seconds and no immediate messages
            elif self.message_text and not immediate_messages:
                self.message_text = ""
                self.update_message(self.message_text)
            
            # If any habit is currently detected (but not for 3 seconds yet),
            # keep the outline visible and reset the last detection time
            if any_habit_detected and self.is_showing:
                self.last_detection_time = current_time
            # Otherwise, check if we should show green feedback or hide the outline
            elif not any_habit_detected and current_time - self.last_detection_time >= self.clear_threshold:
                if self.is_showing:
                    # Also hide the tint if it's showing
                    if self.is_tinted:
                        self.hide_tint()
                    # Show green outline for positive feedback
                    self.show_outline("green2")
                    self.green_feedback_active = True
                    self.green_start_time = current_time
                    # Don't show notification for green feedback
                    if self.notification_window and self.notification_visible:
                        self.notification_window.withdraw()
                        self.notification_visible = False
    
    def cleanup(self):
        """Clean up resources"""
        if self.root:
            try:
                # Stop audio if it's playing
                if self.audio_playing:
                    self.stop_audio()
                
                # Clean up pygame resources
                if self.audio_initialized:
                    pygame.mixer.quit()
                
                # Flag shutdown
                self.shutdown_requested = True
            except Exception as e:
                print(f"Warning during cleanup: {e}")
    
    def _check_shutdown(self):
        """Check if shutdown was requested and schedule next check"""
        if self.shutdown_requested:
            # Call destroy_root which will handle the shutdown safely
            self._destroy_root()
            return  # Don't schedule another check
        else:
            # Schedule next check
            if self.root:
                self.root.after(100, self._check_shutdown)
    
    def _destroy_root(self):
        """Safely destroy the root window from the main thread"""
        try:
            # Stop audio if it's playing
            if self.audio_playing:
                self.stop_audio()
            
            # Hide all windows first
            for window in self.windows:
                window.withdraw()
            
            # Hide notification window if it exists
            if self.notification_window:
                self.notification_window.withdraw()
            
            # Hide tint window if it exists
            if self.tint_window:
                self.tint_window.withdraw()
            
            # Schedule actual destruction after a short delay
            # This gives time for any pending operations to complete
            self.root.after(200, self._final_destroy)
        except Exception as e:
            print(f"Warning during window destruction: {e}")
        
    def _final_destroy(self):
        """Final destruction of tkinter resources"""
        try:
            # Clean up pygame resources
            if self.audio_initialized:
                pygame.mixer.quit()
                self.audio_initialized = False
                self.beep_sound = None
            
            # Destroy all windows
            for window in self.windows:
                window.destroy()
            self.windows = []
            
            # Destroy notification window if it exists
            if self.notification_window:
                self.notification_window.destroy()
                self.notification_window = None
            
            # Destroy tint window if it exists
            if self.tint_window:
                self.tint_window.destroy()
                self.tint_window = None
            
            # Quit and destroy root
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            print(f"Warning during final destruction: {e}")

    def show_tint(self):
        """Show the red screen tint"""
        if not self.root or not self.tint_window:
            return
        
        # Configure the tint window with red background
        canvas = self.tint_window.winfo_children()[0]
        canvas.configure(bg = "red")
        
        # Show the tint window
        self.tint_window.deiconify()
        self.is_tinted = True
        
        # Record the time when the tint was shown
        self.tint_start_time = time.time()
        
        # Schedule audio check
        if self.audio_initialized:
            self.root.after(int(self.escalation_threshold * 1000), self._check_audio_start)

    def hide_tint(self):
        """Hide the screen tint"""
        if not self.root or not self.tint_window:
            return
        
        # Hide the tint window
        self.tint_window.withdraw()
        self.is_tinted = False
        
        # Stop audio if it's playing
        if self.audio_playing:
            self.stop_audio()

    def _check_audio_start(self):
        """Check if audio should start playing based on tint duration"""
        if not self.root or not self.is_tinted:
            return
        
        current_time = time.time()
        # If tint has been showing for escalation_threshold seconds, start audio
        if current_time - self.tint_start_time >= self.escalation_threshold and self.is_tinted:
            if self.audio_initialized and not self.audio_playing:
                self.start_audio()
                # Schedule the beep to play repeatedly
                self._play_beep_loop()

    def _play_beep_loop(self):
        """Play the beep sound in a loop while audio is playing"""
        if not self.root or not self.audio_playing:
            return
        
        # Play the beep sound
        if self.beep_sound:
            self.beep_sound.play()
        
        # Schedule next beep if audio is still playing
        if self.audio_playing:
            self.root.after(500, self._play_beep_loop)  # Play every second

    def _update_notification_color(self, color):
        """Update the notification window color to match the outline
        
        Args:
            color: Color name ("orange", "red", "green2", etc.)
        """
        if not self.root or not self.notification_window:
            return
            
        canvas = self.notification_window.winfo_children()[0]
        
        # Update background color
        canvas.itemconfig("bg", fill = self._get_notification_bg_color(color))
        
        canvas.itemconfig("title", text = "HabitKicker Alert", fill = "white")
        canvas.itemconfig("line", fill = "gray")
    
    def _get_notification_bg_color(self, outline_color):
        """Get the appropriate notification background color based on outline color
        
        Args:
            outline_color: The current outline color
            
        Returns:
            Appropriate background color for the notification
        """
        if outline_color == "orange":
            return "#663300"  # Dark orange
        elif outline_color == "red":
            return "#660000"  # Dark red
        elif outline_color == "green2":
            return "#006600"  # Dark green
        else:
            return "black"

    def play_beep(self):
        """Play the beep sound"""
        if not self.root or not self.beep_sound:
            return
        
        # Play the beep sound
        self.beep_sound.play()

    def stop_beep(self):
        """Stop the beep sound"""
        if not self.root or not self.beep_sound:
            return
        
        # Stop the beep sound
        self.beep_sound.stop()

    def start_audio(self):
        """Start the audio playback"""
        if not self.root or not self.beep_sound:
            return
        
        # Start the audio playback
        self.audio_playing = True
        # The actual sound playing is handled by _play_beep_loop

    def stop_audio(self):
        """Stop the audio playback"""
        if not self.root or not self.beep_sound:
            return
        
        # Stop the audio playback
        self.audio_playing = False
        if self.beep_sound:
            self.beep_sound.stop()

    def is_audio_playing(self):
        """Check if the audio is currently playing"""
        return self.audio_playing

    def is_audio_initialized(self):
        """Check if the audio is initialized"""
        return self.audio_initialized

    def initialize_audio(self, sound_path):
        """Initialize the audio playback"""
        if not self.root or not sound_path:
            return
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Load the sound file
        self.beep_sound = pygame.mixer.Sound(sound_path)
        self.beep_sound.set_volume(self.alarm_volume)

        # Mark audio as initialized
        self.audio_initialized = True

    def update_audio_state(self):
        """Update the audio state based on the current outline color"""
        if not self.root or not self.beep_sound:
            return
        
        # Check if the current outline color is red
        if self.current_color == "red":
            # Start the audio playback if it's not already playing
            if not self.audio_playing:
                self.start_audio()
        else:
            # Stop the audio playback if it's playing
            self.stop_audio() 