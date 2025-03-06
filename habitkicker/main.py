"""Main entry point for the HabitKicker application"""

import cv2
from habitkicker.camera import Camera

def main():
    """Main function to run the HabitKicker application"""
    camera = Camera()
    try:
        camera.start_camera()
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(camera, 'cap') and camera.cap is not None:
            camera.cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 