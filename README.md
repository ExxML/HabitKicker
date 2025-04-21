# HabitKicker

A computer vision application to detect and break unwanted habits like nail-biting, hair-pulling, and slouching using real-time posture analysis.

## Features

- Real-time habit detection using computer vision
- Posture calibration for personalized monitoring
- Customizable detection settings for:
  - Nail biting distance
  - Hair pulling detection
  - Finger proximity alerts
- User-friendly GUI with dark mode
- Configurable notifications and alerts
- Live camera feed with visual feedback
  - Modifiable FPS **(⭐2-5 FPS is recommended for most systems to conserve resources)**

## Requirements

- Python 3.7 or higher
- Dependencies:
  - OpenCV (opencv-python) >= 4.8.0
  - MediaPipe >= 0.10.0
  - NumPy >= 1.24.0
  - PyQt6 >= 6.4.0
  - QDarkStyle >= 3.1.0
  - Pygame >= 2.1.0

## Installation

1. Clone the repository:
```bash
git clone https://github.com/cmd-Exx/HabitKicker.git
cd HabitKicker
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the application using:

```bash
python -m habitkicker
```

or if installed via pip:

```bash
habitkicker
```

## Getting Started

1. Launch the application
2. Use the "Calibrate Posture" button to set your baseline posture
3. Adjust the detection settings according to your preferences
4. Enable/disable notifications and alerts as needed
5. The application will monitor your habits and provide real-time feedback

## License

This project is licensed under the MIT License.

## Version

Current version: 0.1.0 