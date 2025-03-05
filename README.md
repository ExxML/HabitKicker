# HabitBreaker

A computer vision application that helps detect and break unwanted habits like nail-biting, hair-pulling, and slouching using MediaPipe's face, hand, and pose tracking.

## Features

- Real-time face and hand landmark detection
- Nail-biting detection
- Hair-pulling detection
- Slouch detection with calibration
- Screen outline alerts for persistent habits
- Toggle landmark visualization
- Simple and intuitive interface

## Project Structure

```
HabitBreaker/
├── habitbreaker/                # Main package
│   ├── __init__.py
│   ├── main.py                  # Entry point
│   ├── camera.py                # Main camera interface
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
pip install opencv-python mediapipe numpy

# Run the application as a module
python -m habitbreaker.main
```

## Usage

1. Run the application using one of these methods:
   ```bash
   # If installed as a package
   habitbreaker
   
   # Or directly as a module
   python -m habitbreaker.main
   ```

2. Controls:
   - Press 'q' to quit the application
   - Press 'c' to calibrate posture detection

3. The application will detect and alert you about:
   - Nail biting (fingers near mouth)
   - Hair pulling (fingers near forehead)
   - Slouching (deviation from calibrated posture)

4. Slouch Detection:
   - When you first start the application, it will prompt you to sit up straight for calibration
   - The calibration process takes a few seconds to establish your proper posture
   - After calibration, the application will alert you when you slouch
   - You can recalibrate at any time by pressing 'c'
   - The default slouch detection threshold is 15%
   - The slouch detection works by analyzing upper body posture (shoulders, neck, and head position)

5. Screen Outline Alerts:
   - When a habit is detected consistently for 3+ seconds, a yellow outline appears around your screen
   - Detection messages are displayed in the top-left corner of the screen
   - The outline disappears after no habits are detected for 3 seconds
   - You can continue using your computer normally while the outline is displayed
   - The outline is semi-transparent and designed to be noticeable but not obtrusive

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