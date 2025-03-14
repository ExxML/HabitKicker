# HabitKicker

A computer vision application that helps detect and break unwanted habits like nail-biting, hair-pulling, and slouching using MediaPipe's face, hand, and pose tracking.

## Features

- Real-time face and hand landmark detection
- Nail-biting detection
- Hair-pulling detection
- Slouch detection with calibration
- Screen outline alerts for persistent habits
- Toggle landmark visualization
- Modern PyQt6 GUI interface with dark theme
- Adjustable detection parameters
- Customizable alert settings

## Project Structure

```
HabitKicker/
├── habitkicker/                # Main package
│   ├── __init__.py
│   ├── main.py                  # Entry point
│   ├── camera.py                # Main camera interface
│   ├── gui.py                   # PyQt6 GUI interface
│   ├── config/                  # Configuration
│   │   ├── __init__.py
│   │   └── landmark_config.py
│   ├── detectors/               # Habit detection
│   │   ├── __init__.py
│   │   ├── habit_detector.py
│   │   └── slouch_detector.py   # Posture analysis
│   └── utils/                   # Utilities
│       ├── __init__.py
│       ├── mediapipe_handler.py
│       └── screen_overlay.py    # Screen outline functionality
├── pyproject.toml               # Modern Python packaging
└── README.md                    # Documentation
```

## Installation

### Option 1: Install as a package

```bash
# Install the package in development mode
pip install -e .
```

### Option 2: Run without installing

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application as a module
python -m habitkicker.main
```

## Usage

1. Run the application using one of these methods:
   ```bash
   # If installed as a package
   habitkicker
   
   # Or directly as a module
   python -m habitkicker.main
   ```

2. GUI Interface:
   - The application now features a modern PyQt6 GUI with a dark theme
   - Click "Start HabitKicker" to begin habit detection
   - Click "Calibrate Posture" to calibrate your posture
   - Use sliders to adjust detection sensitivity:
     - Max Nail Biting Distance: Controls how close fingers need to be to mouth to trigger nail-biting detection
     - Max Hair Pulling Distance: Controls how close fingers need to be to hairline to trigger hair-pulling detection
     - Max Finger to Finger Distance: Controls how close fingers need to be to each other for hair-pulling detection
   - Toggle notification and screen outline visibility
   - Adjust alarm volume with the volume slider
   - Toggle camera window visibility with the "Toggle Camera Window" button
   - Click "Stop HabitKicker" to stop the application

3. The application will detect and alert you about:
   - Nail biting (fingers near mouth)
   - Hair pulling (fingers near forehead)
   - Slouching (deviation from calibrated posture)

4. Slouch Detection:
   - When you click "Calibrate Posture", the camera window will appear
   - Sit up straight during the calibration process
   - The calibration process takes a few seconds to establish your proper posture
   - After calibration is complete, the camera window will automatically hide
   - The application will alert you when you slouch
   - You can recalibrate at any time by clicking "Calibrate Posture" again

5. Screen Outline Alerts:
   - When a habit is detected consistently for 3+ seconds, a yellow outline appears around your screen
   - Detection messages are displayed in the top-left corner of the screen
   - You can toggle these alerts on/off in the GUI

## How Slouch Detection Works

The slouch detection feature uses MediaPipe's pose estimation to track key upper body landmarks:

1. **Calibration**: During calibration, the application records your proper posture as a reference.
2. **Analysis**: While running, it continuously compares your current posture to the calibrated reference.
3. **Detection**: Slouching is detected based on three main factors:
   - Vertical change in shoulder position (40% weight)
   - Change in neck-to-nose angle (30% weight)
   - Change in distance between nose and neck (30% weight)
4. **Sensitivity**: The threshold determines how much deviation is allowed before alerting you.

## Requirements

- Python 3.7+ up to 3.10
- OpenCV
- MediaPipe
- NumPy
- Webcam 