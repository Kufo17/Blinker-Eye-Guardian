from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QRect, QPoint, QVariantAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen, QGuiApplication
import numpy as np

class CalibrationOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        if self.parent_window:
            self.parent_window.lang_manager.subscribe(self.update_label_text)
        
        # Window configuration for transparent click-through stay-on-top overlay
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Center layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Text label configuration
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            color: #FAFAFA;
            font-size: 32px;
            font-weight: 500;
            font-family: 'Segoe UI', Arial, sans-serif;
            background: transparent;
        """)
        layout.addWidget(self.label)
        
        self.phase = "instructions"
        self.countdown = 5
        self.update_label_text()
        
        # Get screen size and calculate 13 points
        screen = QGuiApplication.primaryScreen().geometry()
        width = screen.width()
        height = screen.height()
        
        M = 80
        x_left = M
        x_center = width // 2
        x_right = width - M
        
        y_top = M
        y_mid = height // 2
        y_bottom = height - M
        
        self.points = [
            (x_left, y_top),                      # 1: Top-Left
            (x_center, y_top),                    # 2: Top-Center
            (x_right, y_top),                     # 3: Top-Right
            (x_left, y_mid),                      # 4: Mid-Left
            (x_center, y_mid),                    # 5: Center
            (x_right, y_mid),                     # 6: Mid-Right
            (x_left, y_bottom),                   # 7: Bottom-Left
            (x_center, y_bottom),                 # 8: Bottom-Center
            (x_right, y_bottom),                  # 9: Bottom-Right
            (width // 4, height // 4),            # 10: Upper-Left Inner
            (3 * width // 4, height // 4),        # 11: Upper-Right Inner
            (width // 4, 3 * height // 4),        # 12: Lower-Left Inner
            (3 * width // 4, 3 * height // 4)     # 13: Lower-Right Inner
        ]
        
        self.current_point_index = 0
        self.target_x = self.points[0][0]
        self.target_y = self.points[0][1]
        
        self.calibration_ears = []
        self.verification_count = 0
        
        # Position animation config
        self.pos_anim = QVariantAnimation(self)
        self.pos_anim.setDuration(650)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.pos_anim.valueChanged.connect(self.on_anim_value_changed)
        
        # Connect thread signals
        if self.parent_window and self.parent_window.thread:
            self.parent_window.thread.ear_updated.connect(self.on_ear_updated)
            self.parent_window.thread.blink_detected.connect(self.on_verification_blink)
            
        # Countdown timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)
        
        # Make the window fullscreen
        self.showFullScreen()
        
    def update_label_text(self):
        if self.parent_window:
            title = self.parent_window.lang_manager.translate("calib_instr_title")
            desc = self.parent_window.lang_manager.translate("calib_instr_desc")
            start = self.parent_window.lang_manager.translate("calib_instr_start", countdown=self.countdown)
            text = f"{title}\n\n{desc}\n\n{start}"
        else:
            text = f"Calibration\n\nPlease follow the moving circle with your eyes and blink once at each position.\n\nStarting in: {self.countdown}"
        self.label.setText(text)

    def update_countdown(self):
        self.countdown -= 1
        if self.countdown > 0:
            self.update_label_text()
        else:
            self.timer.stop()
            self.label.hide()
            self.phase = "circle"
            self.current_point_index = 0
            
            # Start first point immediately at its target position
            self.target_x = self.points[0][0]
            self.target_y = self.points[0][1]
            
            # Start 3-second point movement timer
            self.point_timer = QTimer(self)
            self.point_timer.timeout.connect(self.next_point)
            self.point_timer.start(3000)
            
            self.update()

    def next_point(self):
        self.current_point_index += 1
        if self.current_point_index < len(self.points):
            start_pos = QPoint(self.target_x, self.target_y)
            next_pt = self.points[self.current_point_index]
            end_pos = QPoint(next_pt[0], next_pt[1])
            
            self.pos_anim.setStartValue(start_pos)
            self.pos_anim.setEndValue(end_pos)
            self.pos_anim.start()
        else:
            self.point_timer.stop()
            self.calculate_and_start_verification()

    def on_anim_value_changed(self, value):
        self.target_x = value.x()
        self.target_y = value.y()
        self.update()

    def on_ear_updated(self, ear_value):
        if self.phase == "circle":
            self.calibration_ears.append(ear_value)

    def calculate_and_start_verification(self):
        self.phase = "verification"
        self.verification_count = 0
        
        # Calculate custom threshold
        if len(self.calibration_ears) > 0:
            sorted_ears = sorted(self.calibration_ears)
            n = len(sorted_ears)
            top_n = max(1, int(n * 0.3))
            bottom_n = max(1, int(n * 0.05))
            
            avg_open_ear = float(np.mean(sorted_ears[-top_n:]))
            avg_closed_ear = float(np.mean(sorted_ears[:bottom_n]))
            threshold = avg_closed_ear + 0.3 * (avg_open_ear - avg_closed_ear)
        else:
            avg_open_ear = 0.3
            avg_closed_ear = 0.15
            threshold = 0.21
            
        # Apply parameters to tracking thread
        if self.parent_window and self.parent_window.thread:
            self.parent_window.thread.threshold = threshold
            self.parent_window.thread.avg_open_ear = avg_open_ear
            self.parent_window.thread.min_closed_ear = avg_closed_ear
            self.parent_window.thread.calibrated = True
            
        # Update text for verification
        self.label.show()
        if self.parent_window:
            self.label.setText(self.parent_window.lang_manager.translate("calib_verify"))
        else:
            self.label.setText("Excellent! Now blink 3 times to verify.")
            
        self.update()

    def on_verification_blink(self):
        if self.phase == "verification":
            self.verification_count += 1
            self.update()
            if self.verification_count >= 3:
                self.finish_calibration()

    def finish_calibration(self):
        if self.parent_window:
            # Set calibrated to True
            self.parent_window.thread.calibrated = True
            
            # Save configuration to file
            self.parent_window.save_config()
            
            # Update main window status
            self.parent_window.set_status_from_text(self.parent_window.get_translation("status_config_loaded"))
            self.parent_window.set_status_led("#3B82F6")  # Blue
            
            # Make "Start Tracking" button active and update state
            self.parent_window.btn_toggle.setEnabled(True)
            self.parent_window.update_toggle_button_state()
            
            # If tracking is currently active, start session
            if self.parent_window.tracking_active:
                self.parent_window.start_session()
                
        self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Slate background color: rgba(15, 23, 42, 0.95) -> 15, 23, 42, Alpha = 242
        painter.fillRect(self.rect(), QColor(15, 23, 42, 242))
        
        if self.phase == "circle":
            # Draw clean solid lavender circle of diameter 40px at current coordinates
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#A78BFA"))
            painter.drawEllipse(self.target_x - 20, self.target_y - 20, 40, 40)
            
        elif self.phase == "verification":
            # Draw 3 small indicators (diameter 20px) under the centered text
            center_x = self.width() // 2
            y_pos = self.height() // 2 + 100
            
            dots_x = [center_x - 35, center_x - 10, center_x + 15]
            for i in range(3):
                color = QColor("#10B981") if i < self.verification_count else QColor("#52525B")
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                painter.drawEllipse(dots_x[i], y_pos, 20, 20)

    def closeEvent(self, event):
        # Disconnect signals to prevent dangling references/leaks
        if self.parent_window:
            self.parent_window.lang_manager.unsubscribe(self.update_label_text)
            if self.parent_window.thread:
                try:
                    self.parent_window.thread.ear_updated.disconnect(self.on_ear_updated)
                except TypeError:
                    pass
                try:
                    self.parent_window.thread.blink_detected.disconnect(self.on_verification_blink)
                except TypeError:
                    pass
        super().closeEvent(event)
