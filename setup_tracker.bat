@echo off
python -m pip install --upgrade pip
pip install pyinstaller pywin32 scikit-learn pyqt5 numpy opencv-python pyautogui pynput
pyinstaller --onefile --windowed --icon=icon.ico --add-data "icon.png;." --name BO6_Color_Tracker bo6_tracker.py
pause
