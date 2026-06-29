from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QGuiApplication

class ProgressBarOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        # Configure window flags for a click-through stays-on-top thin overlay bar
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Set geometry: thin bar centered at the very top of the screen
        screen = QGuiApplication.primaryScreen().geometry()
        self.bar_width = 350
        self.bar_height = 6
        x = (screen.width() - self.bar_width) // 2
        y = 0
        self.setGeometry(x, y, self.bar_width, self.bar_height)
        
        self.progress_pct = 0.0  # From 0.0 to 1.0
        self.dark_mode = False

    def set_dark_mode(self, is_dark):
        self.dark_mode = is_dark
        self.update()

    def set_progress(self, pct, color_hex=None):
        """Updates the progress percentage, then schedules a repaint."""
        self.progress_pct = max(0.0, min(1.0, pct))
        self.update()

    def interpolate_color(self, color1, color2, t):
        # t - value from 0.0 to 1.0
        r = int(color1.red() * (1 - t) + color2.red() * t)
        g = int(color1.green() * (1 - t) + color2.green() * t)
        b = int(color1.blue() * (1 - t) + color2.blue() * t)
        return QColor(r, g, b)

    def paintEvent(self, event):
        """Renders the custom progress bar overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background track
        bg_color = QColor("#27272A") if self.dark_mode else QColor("#E2E8F0")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 3.0, 3.0)
        
        # Draw active progress fill
        fill_width = int(self.bar_width * self.progress_pct)
        if fill_width > 0:
            green = QColor("#10B981")
            orange = QColor("#F59E0B")
            red = QColor("#EF4444")
            
            ratio = self.progress_pct
            if ratio <= 0.5:
                t = ratio / 0.5
                color = self.interpolate_color(green, orange, t)
            else:
                t = (ratio - 0.5) / 0.5
                color = self.interpolate_color(orange, red, t)
                
            painter.setBrush(color)
            painter.drawRoundedRect(0, 0, fill_width, self.bar_height, 3.0, 3.0)
