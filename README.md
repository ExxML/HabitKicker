# HabitKicker

A computer vision application to detect and break unwanted habits like nail-biting, hair-pulling, and slouching using real-time posture analysis.

## Features

- Real-time habit detection using computer vision
- Posture calibration for personalized monitoring
- Customizable detection settings for:
  - Nail biting distance (distance from finger to mouth)
  - Hair pulling distance (distance from finger to hair)
- User-friendly GUI with dark mode
- Configurable notifications and alerts
- Live camera feed with visual feedback
  - Modifiable FPS **(⭐2-5 FPS is recommended for most systems to conserve resources)**

## Requirements

- Python 3.10.11
- Dependencies:
  - OpenCV (opencv-python) == 4.11.0.86
  - MediaPipe == 0.10.14
  - PyQt6 == 6.8.1
  - QDarkStyle == 3.2.3
  - Pygame == 2.6.1

## Installation

1. Clone the repository:
```bash
git clone https://github.com/cmd-Exx/HabitKicker.git
cd HabitKicker
```

2. Create and activate a local environment:
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the application using HabitKicker.exe

or from source:

```bash
python -m habitkicker.main
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