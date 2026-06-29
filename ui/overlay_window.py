from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor

class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        
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
        self.label = QLabel("Кліпни повністю! 👁️", self)
        self.label.setStyleSheet("""
            color: #ff4d4d;
            font-size: 56px;
            font-weight: bold;
            font-family: 'Segoe UI', Arial, sans-serif;
            background: transparent;
        """)
        layout.addWidget(self.label)
        
        # Add a soft pulse animation to the text using opacity
        self.opacity_effect = QGraphicsOpacityEffect(self.label)
        self.label.setGraphicsEffect(self.opacity_effect)
        
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(1200)
        self.animation.setStartValue(0.2)
        self.animation.setKeyValueAt(0.5, 1.0)
        self.animation.setEndValue(0.2)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.setLoopCount(-1) # Loop infinitely
        self.animation.start()
        
        # Make the window fullscreen
        self.showFullScreen()

    def paintEvent(self, event):
        """Draws the semi-transparent red overlay background."""
        painter = QPainter(self)
        # rgba(220, 53, 69, 0.15) -> 220, 53, 69, Alpha = 38 (out of 255)
        painter.fillRect(self.rect(), QColor(220, 53, 69, 38))
