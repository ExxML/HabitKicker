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
- Live camera feed with visual feedback (press `Ctrl+T` to open/close)
  - Modifiable FPS **(⭐2-5 FPS is recommended for most systems to conserve resources)**

## Requirements

- Python 3.12.10
- Dependencies:
  - OpenCV (opencv-python) == 4.11.0.86
  - MediaPipe == 0.10.14
  - PyQt6 == 6.8.1
  - QDarkStyle == 3.2.3
  - Pygame == 2.6.1
- Hardware:
  - Minimum 480p webcam

## Installation

Run the application using HabitKicker.exe in Releases

Or from source:

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

4. Run in terminal:
```bash
python habitkicker\main.py
```

## Getting Started

1. Launch the application
2. Use the "Calibrate Posture" button (or press `Ctrl+C`) to set your baseline posture
3. Adjust the detection settings according to your preferences
4. Enable/disable notifications and alerts as needed
5. The application will monitor your habits and provide real-time feedback

## Compile to .exe Using Nuitka

1. Install Nuitka:
```bash
pip install nuitka
```

2. Generate .exe:
```bash
python -m nuitka --standalone --windows-icon-from-ico="data/HabitKicker.ico" --windows-console-mode=disable --enable-plugin=pyqt6 --enable-plugin=tk-inter --include-data-dir=".venv\Lib\site-packages\mediapipe\modules=mediapipe/modules" --include-data-dir="data=data" --include-data-dir="sounds=sounds" habitkicker\main.py
```

3. [Optional] Auto-run on startup:
- Create a shortcut for `main.exe`
- Move the shortcut to the Startup folder (Press `Win+R`, then type `shell:startup`)

## License

This project is licensed under the MIT License.

## Version

Current version: 1.0 