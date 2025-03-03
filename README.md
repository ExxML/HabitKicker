# HabitBreaker

A computer vision application that helps detect and break unwanted habits like nail-biting, hair-pulling, and slouching using MediaPipe's face, hand, and pose tracking.

## Features

- Real-time face and hand landmark detection
- Nail-biting detection
- Hair-pulling detection
- Slouching detection for seated users
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
│   │   └── habit_detector.py
│   └── utils/                   # Utilities
│       ├── __init__.py
│       └── mediapipe_handler.py
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

3. The application will detect and alert you about:
   - Nail biting (fingers near mouth)
   - Hair pulling (fingers near forehead)
   - Slouching (poor upper body posture)

## Requirements

- Python 3.7+
- OpenCV
- MediaPipe
- NumPy
- Webcam 