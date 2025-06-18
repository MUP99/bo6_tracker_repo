import sys
import cv2
import numpy as np
import pyautogui
import time
import random
from pynput.mouse import Controller
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, 
                            QWidget, QVBoxLayout, QLabel, QPushButton, 
                            QComboBox, QSpinBox, QColorDialog, QMessageBox)
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from sklearn.cluster import KMeans

class TrackerThread(QThread):
    update_signal = pyqtSignal(str)
    target_found = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self.target_color = np.array([201, 0, 141])  # Pink color #C9008D in RGB
        self.tolerance = 30
        self.running = False
        self.speed = 0.7
        self.mouse = Controller()
        self.kmeans = KMeans(n_clusters=3)

    def run(self):
        self.running = True
        self.update_signal.emit("Tracking started...")
        
        while self.running:
            try:
                start_time = time.time()
                
                screenshot = pyautogui.screenshot()
                image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                target_pos = self.detect_color(image)
                if target_pos:
                    self.target_found.emit(*target_pos)
                    self.move_mouse(*target_pos)
                
                processing_time = time.time() - start_time
                sleep_time = max(0.01, 0.1 - processing_time)
                time.sleep(sleep_time)
                
            except Exception as e:
                self.update_signal.emit(f"Error: {str(e)}")
                time.sleep(1)

    def detect_color(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        combined = np.concatenate([image, hsv, lab], axis=2)
        
        pixels = combined.reshape((-1, 3))
        self.kmeans.fit(pixels)
        target_label = self.kmeans.predict([self.target_color])[0]
        mask = self.kmeans.labels_.reshape(image.shape[:2]) == target_label
        
        contours, _ = cv2.findContours(mask.astype(np.uint8),
                                     cv2.RETR_EXTERNAL,
                                     cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > 20:
                M = cv2.moments(largest)
                if M["m00"] != 0:
                    return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        return None

    def move_mouse(self, x, y):
        current_x, current_y = self.mouse.position
        distance = ((x - current_x)**2 + (y - current_y)**2)**0.5
        if distance < 5:
            self.mouse.position = (x, y)
            return
        
        steps = max(5, int(distance * self.speed * 0.3))
        control_x = current_x + (x - current_x)*0.5 + random.uniform(-30, 30)
        control_y = current_y + (y - current_y)*0.5 + random.uniform(-30, 30)
        
        for t in np.linspace(0, 1, steps):
            bezier_x = (1-t)**2*current_x + 2*(1-t)*t*control_x + t**2*x
            bezier_y = (1-t)**2*current_y + 2*(1-t)*t*control_y + t**2*y
            if t < 0.9:
                bezier_x += random.gauss(0, 1.5)
                bezier_y += random.gauss(0, 1.5)
            self.mouse.position = (bezier_x, bezier_y)
            time.sleep(random.uniform(0.001, 0.003))

    def stop(self):
        self.running = False
        self.wait()
        self.update_signal.emit("Tracking stopped")


class ColorTrackerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.tracker = TrackerThread()
        self.init_ui()
        self.init_tray_icon()
        self.tracker.update_signal.connect(self.update_status)
        self.tracker.target_found.connect(self.on_target_found)

    def init_ui(self):
        self.setWindowTitle("BO6 Color Tracker")
        self.setWindowIcon(QIcon('icon.png'))
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        self.status_label = QLabel("Status: Inactive")
        layout.addWidget(self.status_label)
        
        self.color_btn = QPushButton("Select Target Color")
        self.color_btn.clicked.connect(self.choose_color)
        layout.addWidget(self.color_btn)
        
        self.tolerance_spin = QSpinBox()
        self.tolerance_spin.setRange(0, 100)
        self.tolerance_spin.setValue(30)
        self.tolerance_spin.valueChanged.connect(self.update_tolerance)
        layout.addWidget(QLabel("Color Tolerance:"))
        layout.addWidget(self.tolerance_spin)
        
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["Slow", "Medium", "Fast"])
        self.speed_combo.setCurrentIndex(1)
        self.speed_combo.currentIndexChanged.connect(self.update_speed)
        layout.addWidget(QLabel("Movement Speed:"))
        layout.addWidget(self.speed_combo)
        
        self.start_btn = QPushButton("Start Tracking")
        self.start_btn.clicked.connect(self.start_tracking)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Tracking")
        self.stop_btn.clicked.connect(self.stop_tracking)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)
        
        self.setLayout(layout)

    def init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('icon.png'))
        
        menu = QMenu()
        show_action = menu.addAction("Show Window")
        show_action.triggered.connect(self.show)
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.close_app)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.tray_icon_clicked)

    def tray_icon_clicked(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.tracker.target_color = np.array([color.red(), color.green(), color.blue()])
            self.color_btn.setStyleSheet(f"background-color: {color.name()}")

    def update_tolerance(self, value):
        self.tracker.tolerance = value

    def update_speed(self, index):
        speeds = [0.3, 0.7, 1.0]
        self.tracker.speed = speeds[index]

    def start_tracking(self):
        if not self.tracker.isRunning():
            self.tracker.start()
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("Status: Tracking...")

    def stop_tracking(self):
        if self.tracker.isRunning():
            self.tracker.stop()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("Status: Inactive")

    def on_target_found(self, x, y):
        self.status_label.setText(f"Status: Target at ({x}, {y})")

    def update_status(self, message):
        self.status_label.setText(f"Status: {message}")

    def close_app(self):
        self.tracker.stop()
        self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "BO6 Color Tracker",
            "App is running in background. Double-click tray icon to show.",
            QSystemTrayIcon.Information,
            2000
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("System tray not available")
        msg.exec_()
        sys.exit(1)
    window = ColorTrackerApp()
    window.show()
    sys.exit(app.exec_())
