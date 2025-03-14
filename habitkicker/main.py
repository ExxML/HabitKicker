"""Main entry point for the HabitKicker application"""

import sys
from PyQt6.QtWidgets import QApplication
from habitkicker.gui import HabitKickerGUI

def main():
    """Main function to run the HabitKicker application"""
    app = QApplication(sys.argv)
    
    # Create and show the GUI
    window = HabitKickerGUI()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 