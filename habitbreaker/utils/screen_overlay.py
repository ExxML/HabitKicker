"""Module for creating screen overlays and outlines"""

import cv2
import numpy as np
import time
import threading
import tkinter as tk
from tkinter import Toplevel, Canvas

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
        self.habit_status = {
            'nail_biting': {'active': False, 'start_time': 0},
            'hair_pulling': {'active': False, 'start_time': 0},
            'slouching': {'active': False, 'start_time': 0}
        }
        self.detection_threshold = 3.0  # seconds
        self.clear_threshold = 3.0  # seconds
        self.last_detection_time = 0
        self.message_text = ""
        
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
        canvas.create_text(10, 20, anchor = "nw", text = "", fill = "red", font = ("Arial", 14), tags = "message")
        
        return window
    
    def show_outline(self, color):
        """Show the outline with the specified color
        
        Args:
            color: Color name ("orange", "red", etc.)
        """
        if not self.root or not self.windows:
            return
            
        self.current_color = color
        
        # Update all outline windows
        for window in self.windows[:-1]:  # Skip message window
            canvas = window.winfo_children()[0]
            canvas.configure(bg = color)
        
        # Show all windows
        for window in self.windows:
            window.deiconify()
            
        self.is_showing = True
    
    def hide_outline(self):
        """Hide the outline"""
        if not self.root or not self.windows:
            return
            
        # Hide all windows
        for window in self.windows:
            window.withdraw()
            
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
        
        # Update text
        canvas.itemconfig("message", text = message)
    
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
            
            # Show outline if not already showing
            if not self.is_showing:
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
            # Otherwise, check if we should hide the outline (after 3 seconds of no detection)
            elif not any_habit_detected and current_time - self.last_detection_time >= self.clear_threshold:
                if self.is_showing:
                    self.hide_outline()
    
    def cleanup(self):
        """Clean up resources"""
        if self.root:
            self.root.quit()
            self.root.destroy() 