# BO6 Color Tracker

هذا المشروع يحتوي على سكربت بايثون لتحريك الماوس باتجاه لون معين (`#C9008D` افتراضياً) باستخدام PyQt5 لواجهة المستخدم.

## كيفية البناء محلياً

```bash
# تثبيت الحزم:
pip install pyinstaller pywin32 scikit-learn pyqt5 numpy opencv-python pyautogui pynput

# بناء EXE:
pyinstaller --onefile --windowed --icon=icon.ico --add-data "icon.png;." --name BO6_Color_Tracker bo6_tracker.py
```

## CI/CD عبر GitHub Actions
- يدعم البناء على Windows وتنتج ملف `BO6_Color_Tracker.exe` في قسم الـ Artifacts.
