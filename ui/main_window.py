import time
import webbrowser
import sys
import os
import winreg
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSlider, QLabel, QProgressBar, QCheckBox, QFrame, QLayout,
    QSizePolicy, QComboBox, QSystemTrayIcon, QMenu, QDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QPoint, QPointF, QThread, pyqtSignal
from PyQt6.QtGui import (
    QImage, QPixmap, QAction, QIcon, QPainter, QPainterPath,
    QColor, QBrush, QPen, QLinearGradient
)
from tracking_thread import TrackingThread
from ui.progress_bar_overlay import ProgressBarOverlay
from ui.calibration_overlay import CalibrationOverlay

def generate_check_icon():
    import os
    os.makedirs("ui", exist_ok=True)
    check_path = os.path.join("ui", "check.png")
    if not os.path.exists(check_path):
        from PyQt6.QtGui import QImage, QPainter, QPen, QColor
        from PyQt6.QtCore import Qt
        img = QImage(16, 16, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor("#FFFFFF"))
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        painter.drawLine(3, 8, 7, 12)
        painter.drawLine(7, 12, 13, 4)
        painter.end()
        
        img.save(check_path)

generate_check_icon()

def generate_flag_icons():
    import os
    os.makedirs("ui", exist_ok=True)
    flag_ua_path = os.path.join("ui", "flag_ua.png")
    flag_en_path = os.path.join("ui", "flag_en.png")
    flag_es_path = os.path.join("ui", "flag_es.png")
    
    from PyQt6.QtGui import QImage, QPainter, QColor, QBrush, QPen
    from PyQt6.QtCore import Qt, QRectF
    
    if not os.path.exists(flag_ua_path):
        img_ua = QImage(20, 15, QImage.Format.Format_ARGB32)
        painter = QPainter(img_ua)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(QRectF(0, 0, 20, 7.5), QBrush(QColor("#0057B7")))
        painter.fillRect(QRectF(0, 7.5, 20, 7.5), QBrush(QColor("#FFD700")))
        painter.end()
        img_ua.save(flag_ua_path)
        
    if not os.path.exists(flag_en_path):
        img_en = QImage(20, 15, QImage.Format.Format_ARGB32)
        img_en.fill(Qt.GlobalColor.white)
        painter = QPainter(img_en)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        red_color = QColor("#B22234")
        stripe_h = 15.0 / 7.0
        for i in range(7):
            if i % 2 == 0:
                painter.fillRect(QRectF(0, i * stripe_h, 20, stripe_h), QBrush(red_color))
        painter.fillRect(QRectF(0, 0, 9, 8), QBrush(QColor("#3C3B6E")))
        painter.setPen(QPen(QColor("#FFFFFF")))
        painter.drawPoint(2, 2)
        painter.drawPoint(6, 2)
        painter.drawPoint(4, 4)
        painter.drawPoint(2, 6)
        painter.drawPoint(6, 6)
        painter.end()
        img_en.save(flag_en_path)

    if not os.path.exists(flag_es_path):
        img_es = QImage(20, 15, QImage.Format.Format_ARGB32)
        painter = QPainter(img_es)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(QRectF(0, 0, 20, 3.75), QBrush(QColor("#AD1519")))
        painter.fillRect(QRectF(0, 3.75, 20, 7.5), QBrush(QColor("#FFC400")))
        painter.fillRect(QRectF(0, 11.25, 20, 3.75), QBrush(QColor("#AD1519")))
        painter.end()
        img_es.save(flag_es_path)

generate_flag_icons()

class SparkWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.dark_mode = False

    def set_dark_mode(self, is_dark):
        self.dark_mode = is_dark
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor("#14B8A6"))
        pen.setWidthF(3.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Draw 3 thick capsule rays spreading from right-bottom area
        painter.drawLine(13, 17, 5, 16)
        painter.drawLine(14, 12, 8, 6)
        painter.drawLine(19, 10, 17, 3)

class ToggleButtonIconWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(14, 14)
        self.is_stop = False
        
    def set_mode(self, is_stop):
        self.is_stop = is_stop
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(Qt.PenStyle.NoPen)
        
        if self.is_stop:
            # Draw a rounded square
            rect = self.rect()
            r = rect.adjusted(1, 1, -1, -1)
            painter.drawRoundedRect(r, 3, 3)
        else:
            # Draw a play triangle
            w = self.width()
            h = self.height()
            path = QPainterPath()
            path.moveTo(w * 0.25, h * 0.15)
            path.lineTo(w * 0.25, h * 0.85)
            path.lineTo(w * 0.85, h * 0.5)
            path.closeSubpath()
            painter.drawPath(path)

class TargetIconWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.dark_mode = False
        
    def set_dark_mode(self, is_dark):
        self.dark_mode = is_dark
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        color_hex = "#14B8A6" if self.dark_mode else "#0D9488"
        pen = QPen(QColor(color_hex))
        pen.setWidthF(1.2)
        painter.setPen(pen)
        
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        r = 5.0
        
        # Circle
        painter.drawEllipse(QPointF(cx, cy), r, r)
        
        # Center dot
        painter.setBrush(QBrush(QColor(color_hex)))
        painter.drawEllipse(QPointF(cx, cy), 1.0, 1.0)
        
        # 4 ticks
        painter.drawLine(QPointF(cx, cy - r - 3), QPointF(cx, cy - r + 1))
        painter.drawLine(QPointF(cx, cy + r - 1), QPointF(cx, cy + r + 3))
        painter.drawLine(QPointF(cx - r - 3, cy), QPointF(cx - r + 1, cy))
        painter.drawLine(QPointF(cx + r - 1, cy), QPointF(cx + r + 3, cy))

class ScanIconWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.dark_mode = False
        
    def set_dark_mode(self, is_dark):
        self.dark_mode = is_dark
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background card
        bg_color = QColor("#18181B" if self.dark_mode else "#E0F2FE")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)
        
        color = QColor("#14B8A6" if self.dark_mode else "#0D9488")
        pen = QPen(color)
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Corner brackets
        # Top-left
        painter.drawPolyline([
            QPoint(12, 16),
            QPoint(12, 12),
            QPoint(16, 12)
        ])
        # Top-right
        painter.drawPolyline([
            QPoint(24, 12),
            QPoint(28, 12),
            QPoint(28, 16)
        ])
        # Bottom-left
        painter.drawPolyline([
            QPoint(12, 24),
            QPoint(12, 28),
            QPoint(16, 28)
        ])
        # Bottom-right
        painter.drawPolyline([
            QPoint(24, 28),
            QPoint(28, 28),
            QPoint(28, 24)
        ])
        
        # Smiley face
        # Eyes
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(16, 17, 2, 2)
        painter.drawEllipse(22, 17, 2, 2)
        
        # Smile
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(17, 18, 6, 6, -30 * 16, -120 * 16)

class PulseIconWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 16)
        self.dark_mode = False
        
    def set_dark_mode(self, is_dark):
        self.dark_mode = is_dark
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        color_hex = "#14B8A6" if self.dark_mode else "#0D9488"
        pen = QPen(QColor(color_hex))
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        path = QPainterPath()
        path.moveTo(0, 8)
        path.lineTo(6, 8)
        path.lineTo(9, 2)
        path.lineTo(12, 14)
        path.lineTo(15, 4)
        path.lineTo(17, 8)
        path.lineTo(24, 8)
        
        painter.drawPath(path)

class CustomProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.min_value = 0
        self.max_value = 100
        self.dark_mode = False
        self.setFixedHeight(16)

    def setValue(self, value):
        self.value = value
        self.update()

    def setRange(self, min_val, max_val):
        self.min_value = min_val
        self.max_value = max_val
        self.update()

    def set_dark_mode(self, is_dark):
        self.dark_mode = is_dark
        self.update()

    def interpolate_color(self, color1, color2, t):
        # t - value from 0.0 to 1.0
        r = int(color1.red() * (1 - t) + color2.red() * t)
        g = int(color1.green() * (1 - t) + color2.green() * t)
        b = int(color1.blue() * (1 - t) + color2.blue() * t)
        return QColor(r, g, b)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background rounded rect
        bg_color = QColor("#27272A") if self.dark_mode else QColor("#E2E8F0")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        rect = self.rect()
        bg_path = QPainterPath()
        bg_path.addRoundedRect(float(rect.x()), float(rect.y()), float(rect.width()), float(rect.height()), 8.0, 8.0)
        painter.drawPath(bg_path)
        
        # Calculate chunk width
        total_range = self.max_value - self.min_value
        if total_range > 0 and self.value > self.min_value:
            ratio = (self.value - self.min_value) / total_range
            ratio = min(1.0, max(0.0, ratio))
            chunk_width = int(ratio * self.width())
            
            if chunk_width > 0:
                # Dynamic radius to prevent square chunk look at small widths
                r = min(8.0, chunk_width / 2.0)
                
                painter.setClipPath(bg_path)
                
                green = QColor("#10B981")
                orange = QColor("#F59E0B")
                red = QColor("#EF4444")
                
                if ratio <= 0.5:
                    t = ratio / 0.5
                    color = self.interpolate_color(green, orange, t)
                else:
                    t = (ratio - 0.5) / 0.5
                    color = self.interpolate_color(orange, red, t)
                    
                painter.setBrush(QBrush(color))
                painter.drawRoundedRect(0, 0, chunk_width, self.height(), r, r)

LANGUAGES = {
    "en": {
        "title": "Blinker — Your Eye Guardian",
        "subtitle": "Your Eye Guardian",
        "btn_start": "Start Tracking",
        "btn_stop": "Stop Tracking",
        "btn_recalibrate": "Recalibrate",
        "lbl_slider_title": "Remind every",
        "lbl_slider_unit": "sec",
        "chk_preview": "Show camera preview",
        "lbl_ear_title": "Current EAR index",
        "lbl_bpm_title": "Average frequency",
        "preview_disabled": "Preview disabled",
        "preview_waiting": "Waiting for tracking start...",
        "overlay_text": "Blink fully! 👁️",
        "bpm_waiting": "Waiting...",
        "support_kofi": "☕ Buy me a coffee",
        "cb_tray": "Minimize to Tray on Close",
        "cb_autostart": "Launch on Windows Startup",
        "cb_dark_theme": "Dark Theme",
        "tray_show": "Show",
        "tray_exit": "Exit",
        "tray_bubble_title": "Blinker",
        "tray_bubble_msg": "Blinker runs in background! 👁️",
        # Statuses
        "status_stopped": "Tracking stopped",
        "status_stopped_sub": "Ready",
        "status_starting": "Starting camera...",
        "status_starting_sub": "Initializing...",
        "status_face_ok": "Face in frame",
        "status_face_ok_sub": "Tracking active",
        "status_face_night": "Face in frame (Night boost 🌙)",
        "status_face_night_sub": "Tracking active",
        "status_face_lost": "Face not detected (PAUSE)",
        "status_face_lost_sub": "Paused",
        "status_config_loaded": "Calibration loaded",
        "status_config_loaded_sub": "Ready to start",
        "status_calib_req": "Calibration required ⚠️",
        "status_calib_req_sub": "Setup required",
        "status_calib_ok": "Calibration successful",
        "status_calib_ok_sub": "Ready",
        "status_calibrating": "Calibrating...",
        "status_calibrating_sub": "Follow the marker",
        "error_sub": "Error occurred",
        
        # Tooltips
        "ear_tooltip": "Eye Aspect Ratio (EAR) measures eye openness. Lower values indicate closed eyes or blinking.",
        "bpm_tooltip": "Average blink frequency per minute (BPM). Healthy range is 10-15 blinks/min.",
        
        # Settings Dialog
        "settings_title": "Settings",
        "settings_lang": "Language",
        "settings_preview": "Show camera preview",
        "settings_tray": "Minimize to Tray on Close",
        "settings_autostart": "Launch on Windows Startup",
        "settings_close": "Close",
        
        # Calibration Overlay
        "calib_instr_title": "Calibration",
        "calib_instr_desc": "Please follow the moving circle with your eyes and blink once at each position.",
        "calib_instr_start": "Starting in: {countdown}",
        "calib_verify": "Excellent! Now blink 3 times to verify.",
        
        # Update Dialog
        "update_title": "Update Available",
        "update_desc": "A new version of Blinker is available! Would you like to download {version}?",
        "update_btn_download": "Download",
        "update_btn_later": "Later"
    },
    "uk": {
        "title": "Blinker — Охоронець Ваших Очей",
        "subtitle": "Охоронець Ваших Очей",
        "btn_start": "Запустити трекінг",
        "btn_stop": "Зупинити",
        "btn_recalibrate": "Перекалібрувати",
        "lbl_slider_title": "Нагадування кожні",
        "lbl_slider_unit": "сек",
        "chk_preview": "Показувати прев'ю з камери",
        "lbl_ear_title": "Поточний індекс EAR",
        "lbl_bpm_title": "Середня частота",
        "preview_disabled": "Прев'ю вимкнено",
        "preview_waiting": "Очікування запуску трекінгу...",
        "overlay_text": "Кліпни повністю! 👁️",
        "bpm_waiting": "Очікування...",
        "support_kofi": "☕ Підтримати автора",
        "cb_tray": "Згортати в трей при закритті",
        "cb_autostart": "Запускати разом з Windows",
        "cb_dark_theme": "Темна тема",
        "tray_show": "Показати",
        "tray_exit": "Вихід",
        "tray_bubble_title": "Blinker",
        "tray_bubble_msg": "Blinker працює у фоні! 👁️",
        # Statuses
        "status_stopped": "Трекінг зупинено",
        "status_stopped_sub": "Готовий",
        "status_starting": "Запуск камери...",
        "status_starting_sub": "Ініціалізація...",
        "status_face_ok": "Обличчя в кадрі",
        "status_face_ok_sub": "Трекінг активний",
        "status_face_night": "Обличчя в кадрі (Нічний буст 🌙)",
        "status_face_night_sub": "Трекінг активний",
        "status_face_lost": "Обличчя не виявлено (ПАУЗА)",
        "status_face_lost_sub": "Призупинено",
        "status_config_loaded": "Калібрування завантажено",
        "status_config_loaded_sub": "Готовий до запуску",
        "status_calib_req": "Потрібне калібрування ⚠️",
        "status_calib_req_sub": "Потрібне калібрування",
        "status_calib_ok": "Калібрування успішне",
        "status_calib_ok_sub": "Готовий",
        "status_calibrating": "Калібрування...",
        "status_calibrating_sub": "Стежте за маркером",
        "error_sub": "Виникла помилка",
        
        # Tooltips
        "ear_tooltip": "Індекс EAR (Eye Aspect Ratio) вимірює рівень розкриття ока. Менші значення свідчать про закриті очі або кліпання.",
        "bpm_tooltip": "Середня частота кліпання на хвилину (BPM). Нормальний показник: 10-15 кліпань на хвилину.",
        
        # Settings Dialog
        "settings_title": "Налаштування",
        "settings_lang": "Мова",
        "settings_preview": "Показувати прев'ю з камери",
        "settings_tray": "Згортати в трей при закритті",
        "settings_autostart": "Запускати разом з Windows",
        "settings_close": "Закрити",
        
        # Calibration Overlay
        "calib_instr_title": "Калібрування",
        "calib_instr_desc": "Будь ласка, стежте очима за рухомим кружечком і моргайте один раз на кожній позиції.",
        "calib_instr_start": "Початок через: {countdown}",
        "calib_verify": "Чудово! Тепер моргніть 3 рази для перевірки.",
        
        # Update Dialog
        "update_title": "Доступне оновлення",
        "update_desc": "Доступна нова версія Blinker! Бажаєте завантажити оновлення {version}?",
        "update_btn_download": "Завантажити",
        "update_btn_later": "Пізніше"
    },
    "es": {
        "title": "Blinker — Tu guardián ocular",
        "subtitle": "Tu guardián ocular",
        "btn_start": "Iniciar seguimiento",
        "btn_stop": "Detener",
        "btn_recalibrate": "Recalibrar",
        "lbl_slider_title": "Recordar cada",
        "lbl_slider_unit": "seg",
        "chk_preview": "Mostrar vista previa",
        "lbl_ear_title": "Índice EAR actual",
        "lbl_bpm_title": "Frecuencia promedio",
        "preview_disabled": "Vista previa desactivada",
        "preview_waiting": "Esperando inicio de seguimiento...",
        "overlay_text": "¡Parpadea completamente! 👁️",
        "bpm_waiting": "Esperando...",
        "support_kofi": "☕ Cómprame un café",
        "cb_tray": "Minimizar a la bandeja al cerrar",
        "cb_autostart": "Iniciar con Windows",
        "cb_dark_theme": "Tema oscuro",
        "tray_show": "Mostrar",
        "tray_exit": "Salir",
        "tray_bubble_title": "Blinker",
        "tray_bubble_msg": "¡Blinker se ejecuta en segundo plano! 👁️",
        # Statuses
        "status_stopped": "Seguimiento detenido",
        "status_stopped_sub": "Listo",
        "status_starting": "Iniciando cámara...",
        "status_starting_sub": "Inicializando...",
        "status_face_ok": "Rostro en el encuadre",
        "status_face_ok_sub": "Seguimiento activo",
        "status_face_night": "Rostro en el encuadre (Boost nocturno 🌙)",
        "status_face_night_sub": "Seguimiento activo",
        "status_face_lost": "Rostro no detectado (PAUSA)",
        "status_face_lost_sub": "Pausado",
        "status_config_loaded": "Calibración cargada",
        "status_config_loaded_sub": "Listo para comenzar",
        "status_calib_req": "Calibración requerida ⚠️",
        "status_calib_req_sub": "Configuración requerida",
        "status_calib_ok": "Calibración exitosa",
        "status_calib_ok_sub": "Listo",
        "status_calibrating": "Calibrando...",
        "status_calibrating_sub": "Sigue el marcador",
        "error_sub": "Ocurrió un error",
        
        # Tooltips
        "ear_tooltip": "El Índice de Aspecto del Ojo (EAR) mide la apertura del ojo. Valores más bajos indican ojos cerrados o parpadeo.",
        "bpm_tooltip": "Frecuencia promedio de parpadeo por minuto (BPM). El rango saludable es de 10 a 15 parpadeos/min.",
        
        # Settings Dialog
        "settings_title": "Ajustes",
        "settings_lang": "Idioma",
        "settings_preview": "Mostrar vista previa",
        "settings_tray": "Minimizar a la bandeja al cerrar",
        "settings_autostart": "Iniciar con Windows",
        "settings_close": "Cerrar",
        
        # Calibration Overlay
        "calib_instr_title": "Calibración",
        "calib_instr_desc": "Por favor, sigue el círculo en movimiento con los ojos y parpadea una vez en cada posición.",
        "calib_instr_start": "Comenzando en: {countdown}",
        "calib_verify": "¡Excelente! Ahora parpadea 3 veces para verificar.",
        
        # Update Dialog
        "update_title": "Actualización disponible",
        "update_desc": "¡Hay una nueva versión de Blinker disponible! ¿Te gustaría descargar la versión {version}?",
        "update_btn_download": "Descargar",
        "update_btn_later": "Más tarde"
    }
}

class LanguageManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._current_language = "en"
        self._subscribers = []

    @property
    def current_language(self):
        return self._current_language

    @current_language.setter
    def current_language(self, lang):
        if lang in ["en", "uk", "es"] and lang != self._current_language:
            self._current_language = lang
            self.notify_subscribers()

    def subscribe(self, callback):
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback):
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def notify_subscribers(self):
        for callback in list(self._subscribers):
            try:
                callback()
            except Exception as e:
                print(f"Error notifying language subscriber: {e}")

    def translate(self, key, **kwargs):
        raw = LANGUAGES.get(self._current_language, LANGUAGES["en"]).get(key, key)
        if kwargs:
            try:
                return raw.format(**kwargs)
            except Exception:
                pass
        return raw

import urllib.request
import json

class UpdateCheckThread(QThread):
    update_available = pyqtSignal(str)

    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version

    def run(self):
        try:
            req = urllib.request.Request(
                "https://api.github.com/repos/Kufo17/Blinker-Eye-Guardian/releases/latest",
                headers={"User-Agent": "Blinker-App"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    latest_version = data.get("tag_name")
                    if latest_version and self.is_newer(latest_version, self.current_version):
                        self.update_available.emit(latest_version)
        except Exception as e:
            print(f"Error checking for updates: {e}")

    def is_newer(self, latest, current):
        def parse_version(v_str):
            if not v_str:
                return (0, 0)
            v_str = v_str.lower().strip()
            if v_str.startswith("v"):
                v_str = v_str[1:]
            parts = []
            for p in v_str.split("."):
                try:
                    parts.append(int(p))
                except ValueError:
                    parts.append(0)
            return tuple(parts)
        return parse_version(latest) > parse_version(current)


class UpdateDialog(QDialog):
    def __init__(self, parent, new_version):
        super().__init__(parent)
        self.parent_window = parent
        self.new_version = new_version
        self.lang_manager = LanguageManager.get_instance()
        self.lang_manager.subscribe(self.retranslate_dialog)
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.resize(360, 200)
        self.setStyleSheet(self.parent_window.styleSheet())
        self.parent_window._set_title_bar_theme_for_hwnd(int(self.winId()), self.parent_window.dark_theme_state)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Card container
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        # Description label
        self.lbl_desc = QLabel()
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("font-size: 14px; line-height: 1.4;")
        self.lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.lbl_desc)

        layout.addWidget(card)

        # Buttons layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_later = QPushButton()
        self.btn_later.setObjectName("btn_later")
        self.btn_later.setFixedHeight(40)
        self.btn_later.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_later.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_later)

        self.btn_download = QPushButton()
        self.btn_download.setObjectName("btn_download")
        self.btn_download.setFixedHeight(40)
        self.btn_download.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_download.clicked.connect(self.on_download_clicked)
        btn_layout.addWidget(self.btn_download)

        layout.addLayout(btn_layout)

        self.retranslate_dialog()

    def retranslate_dialog(self):
        self.setWindowTitle(self.lang_manager.translate("update_title"))
        desc_text = self.lang_manager.translate("update_desc", version=self.new_version)
        self.lbl_desc.setText(desc_text)
        self.btn_later.setText(self.lang_manager.translate("update_btn_later"))
        self.btn_download.setText(self.lang_manager.translate("update_btn_download"))

    def on_download_clicked(self):
        webbrowser.open("https://github.com/Kufo17/Blinker-Eye-Guardian/releases")
        self.accept()

    def closeEvent(self, event):
        self.lang_manager.unsubscribe(self.retranslate_dialog)
        super().closeEvent(event)

    def accept(self):
        self.lang_manager.unsubscribe(self.retranslate_dialog)
        super().accept()

    def reject(self):
        self.lang_manager.unsubscribe(self.retranslate_dialog)
        super().reject()


class MainWindow(QMainWindow):
    APP_VERSION = "v1.0"

    def __init__(self, overlay_window):
        super().__init__()
        self.overlay_window = overlay_window
        
        # Initialize Localization Manager
        self.lang_manager = LanguageManager.get_instance()
        self.lang_manager.current_language = "en"
        self.lang_manager.subscribe(self.retranslate_ui)
        
        # Window properties - Fixed Size Layout
        self.setWindowTitle("Blinker")
        self.setFixedSize(446, 529)
        
        # State variables
        self.tracking_active = False
        self.face_in_view = False
        self.time_since_last_blink = 0.0
        self.timeout_duration = 12.0
        self.night_boost_on = False
        self.is_loading = False
        self.is_translating = False
        self.force_exit = False
        
        # Settings state variables (consolidated in SettingsDialog)
        self.preview_enabled_state = False
        self.tray_enabled_state = False
        self.autostart_enabled_state = False
        self.dark_theme_state = False
        self.active_dialog = None
        
        # Session state variables
        self.session_active = False
        self.session_active_duration = 0.0
        self.last_active_time = None
        self.total_blinks = 0
        self.current_language = "en"  # Active language
        
        # Initialize Thread
        self.thread = TrackingThread()
        
        # Connect Thread signals
        self.thread.calibration_message.connect(self.on_calibration_message)
        self.thread.blink_detected.connect(self.on_blink_detected)
        self.thread.ear_updated.connect(self.on_ear_updated)
        self.thread.face_detected.connect(self.on_face_detected)
        self.thread.frame_updated.connect(self.on_frame_updated)
        self.thread.status_message.connect(self.on_status_message)
        self.thread.night_boost_active.connect(self.on_night_boost_active)
        self.thread.calibration_finished.connect(self.on_calibration_finished)
        self.thread.calibration_stage_changed.connect(self.on_calibration_stage_changed)
        self.thread.verification_blink.connect(self.on_verification_blink)
        
        # Initialize Floating Progress Bar Overlay
        self.progress_overlay = ProgressBarOverlay()
        self.progress_overlay.hide()
        
        # Initialize UI elements
        self.init_ui()
        
        self.setWindowIcon(QIcon("icon.png"))
        self.setup_tray_icon()
        
        # Load configuration on startup
        self.load_config()
        
        # Main Timer (ticks every 100ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer.start(100)

        # Check for updates in background
        self.update_thread = UpdateCheckThread(self.APP_VERSION)
        self.update_thread.update_available.connect(self.show_update_dialog)
        self.update_thread.start()

    def get_inactive_dot_style(self):
        color = "#27272A" if self.dark_theme_state else "#E2E8F0"
        return f"background-color: {color}; border-radius: 8px;"

    def get_qss(self, is_dark: bool) -> str:
        if is_dark:
            bg = "#09090B"
            card_bg = "#18181B"
            card_border = "1px solid #27272A"
            card_border_color = "#27272A"
            card_radius = "16px"
            text_primary = "#FAFAFA"
            text_secondary = "#A1A1AA"
            text_copyright = "#71717A"
            accent = "#14B8A6"
            accent_text = "#09090B"
            accent_hover = "#2DD4BF"
            accent_pressed = "#0D9488"
            
            accent_gradient = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #0D9488, stop:1 #0284C7)"
            accent_gradient_hover = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #14B8A6, stop:1 #0EA5E9)"
            accent_gradient_pressed = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #0F766E, stop:1 #0369A1)"
            
            btn_recal_bg = "#18181B"
            btn_recal_border = "1px solid #27272A"
            btn_recal_text = "#FAFAFA"
            btn_recal_hover = "#27272A"
            btn_recal_hover_border = "#3F3F46"
            btn_recal_pressed = "#18181B"
            btn_recal_disabled_border = "#1C1C21"
            btn_recal_disabled_text = "#71717A"
            slider_groove = "#27272A"
            slider_handle = "#FAFAFA"
            chk_color = "#FAFAFA"
            chk_indicator_bg = "#18181B"
            chk_indicator_border = "1.5px solid #3F3F46"
            chk_indicator_checked_border = "1.5px solid #14B8A6"
            btn_settings_bg = "#18181B"
            btn_settings_border = "1px solid #27272A"
            btn_settings_text = "#A1A1AA"
            btn_settings_hover_bg = "#27272A"
            btn_settings_hover_text = "#FAFAFA"
            btn_settings_hover_border = "#3F3F46"
            btn_settings_pressed = "#18181B"
            preview_bg = "#000000"
            preview_border = "1px solid #27272A"
            preview_text = "#71717A"
            combo_bg = "#18181B"
            combo_border = "1px solid #27272A"
            combo_view_bg = "#18181B"
            combo_view_border = "1px solid #27272A"
            combo_selection_bg = "#14B8A6"
            combo_selection_text = "#09090B"
            dialog_bg = "#09090B"
            
            scan_bg = "#1E293B"
            scan_color = "#0EA5E9"
            
            kofi_bg = "#18181B"
            kofi_border = "1px solid #14B8A6"
            kofi_circle_bg = "#27272A"
            kofi_circle_color = "#FAFAFA"
            kofi_arrow_color = "#A1A1AA"
            kofi_hover_bg = "#27272A"
            progress_chunk = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #0D9488, stop:1 #0284C7)"
            tooltip_bg = "#1F2937"
            tooltip_color = "#FAFAFA"
        else:
            bg = "#F8FAFC"
            card_bg = "#FFFFFF"
            card_border = "1px solid #E2E8F0"
            card_border_color = "#E2E8F0"
            card_radius = "16px"
            text_primary = "#0F172A"
            text_secondary = "#64748B"
            text_copyright = "#94A3B8"
            accent = "#0D9488"
            accent_text = "#FFFFFF"
            accent_hover = "#0F766E"
            accent_pressed = "#115E59"
            
            accent_gradient = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #14B8A6, stop:1 #0EA5E9)"
            accent_gradient_hover = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #0D9488, stop:1 #0284C7)"
            accent_gradient_pressed = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #0F766E, stop:1 #0369A1)"
            
            btn_recal_bg = "#FFFFFF"
            btn_recal_border = "1px solid #E2E8F0"
            btn_recal_text = "#0F172A"
            btn_recal_hover = "#F8FAFC"
            btn_recal_hover_border = "#CBD5E1"
            btn_recal_pressed = "#F1F5F9"
            btn_recal_disabled_border = "#F8FAFC"
            btn_recal_disabled_text = "#94A3B8"
            slider_groove = "#E2E8F0"
            slider_handle = "#FFFFFF"
            chk_color = "#18181B"
            chk_indicator_bg = "#FFFFFF"
            chk_indicator_border = "1.5px solid #CBD5E1"
            chk_indicator_checked_border = "1.5px solid #14B8A6"
            btn_settings_bg = "#FFFFFF"
            btn_settings_border = "1px solid #E2E8F0"
            btn_settings_text = "#64748B"
            btn_settings_hover_bg = "#F8FAFC"
            btn_settings_hover_text = "#0F172A"
            btn_settings_hover_border = "#CBD5E1"
            btn_settings_pressed = "#F1F5F9"
            preview_bg = "#F8FAFC"
            preview_border = "1px solid #E2E8F0"
            preview_text = "#64748B"
            combo_bg = "#FFFFFF"
            combo_border = "1px solid #E2E8F0"
            combo_view_bg = "#FFFFFF"
            combo_view_border = "1px solid #E2E8F0"
            combo_selection_bg = "#0D9488"
            combo_selection_text = "#FFFFFF"
            dialog_bg = "#F8FAFC"
            
            scan_bg = "#E0F2FE"
            scan_color = "#0284C7"
            
            kofi_bg = "#FFFFFF"
            kofi_border = "1px solid #0D9488"
            kofi_circle_bg = "#FEF3C7"
            kofi_circle_color = "#0F172A"
            kofi_arrow_color = "#64748B"
            kofi_hover_bg = "#F0FDF4"
            progress_chunk = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #14B8A6, stop:1 #0EA5E9)"
            tooltip_bg = "#E2E8F0"
            tooltip_color = "#0F172A"

        return f"""
            QWidget {{
                background-color: {bg};
                color: {text_primary};
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
            }}
            QDialog {{
                background-color: {dialog_bg};
            }}
            QFrame#card {{
                background-color: {card_bg};
                border: {card_border};
                border-radius: {card_radius};
            }}
            QFrame#sep_horiz {{
                background-color: {card_border_color};
                max-height: 1px;
                border: none;
            }}
            QFrame#metric_sep {{
                background-color: {card_border_color};
                max-width: 1px;
                border: none;
            }}
            QLabel {{
                background-color: transparent;
                border: none;
            }}
            QLabel#lbl_title {{
                font-size: 32px;
                font-weight: bold;
                color: {text_primary};
                background: transparent;
            }}
            QLabel#lbl_subtitle {{
                font-size: 13px;
                color: {text_secondary};
                background: transparent;
            }}
            QLabel#lbl_status_title {{
                font-weight: bold;
                font-size: 16px;
                color: {text_primary};
                background: transparent;
            }}
            QLabel#lbl_status_sub {{
                font-size: 11px;
                color: {text_secondary};
                background: transparent;
            }}
            QLabel#lbl_metric_title {{
                font-size: 12px;
                color: {text_secondary};
                background: transparent;
            }}
            QLabel#lbl_metric_val {{
                font-weight: bold;
                font-size: 24px;
                color: {text_primary};
                background: transparent;
            }}
            QLabel#lbl_metric_val_bpm {{
                font-weight: bold;
                font-size: 24px;
                color: {accent};
                background: transparent;
            }}
            QLabel#ear_arrow {{
                color: {accent};
                font-size: 18px;
                font-weight: bold;
                background: transparent;
            }}
            QLabel#bpm_pulse {{
                color: {accent};
                font-size: 18px;
                font-weight: bold;
                background: transparent;
            }}
            QLabel#info_icon {{
                color: #94A3B8;
                font-weight: bold;
                font-size: 12px;
                background: transparent;
            }}
            QLabel#scan_icon {{
                background-color: {scan_bg};
                color: {scan_color};
                font-size: 20px;
                font-weight: bold;
                border-radius: 8px;
            }}
            QLabel#lbl_calibration {{
                color: {accent};
                font-size: 13px;
                font-weight: bold;
                background-color: transparent;
            }}
            QPushButton#btn_toggle {{
                background: {accent_gradient};
                border: none;
                border-radius: 12px;
            }}
            QPushButton#btn_toggle:hover {{
                background: {accent_gradient_hover};
            }}
            QPushButton#btn_toggle:pressed {{
                background: {accent_gradient_pressed};
            }}
            QLabel#toggle_text {{
                color: #FFFFFF;
                font-weight: bold;
                font-size: 14px;
                background: transparent;
            }}
            QLabel#toggle_icon {{
                color: #FFFFFF;
                font-weight: bold;
                font-size: 12px;
                background: transparent;
            }}
            QPushButton#btn_recalibrate {{
                background-color: {btn_recal_bg};
                color: {btn_recal_text};
                border: {btn_recal_border};
                border-radius: 12px;
                padding: 10px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton#btn_recalibrate:hover {{
                background-color: {btn_recal_hover};
                border-color: {btn_recal_hover_border};
            }}
            QPushButton#btn_recalibrate:pressed {{
                background-color: {btn_recal_pressed};
            }}
            QPushButton#btn_recalibrate:disabled {{
                border-color: {btn_recal_disabled_border};
                color: {btn_recal_disabled_text};
            }}
            QLabel#recal_text {{
                color: {btn_recal_text};
                font-weight: bold;
                font-size: 13px;
                background: transparent;
            }}
            QPushButton#btn_recalibrate:disabled QLabel#recal_text {{
                color: {btn_recal_disabled_text};
            }}
            QPushButton#btn_download {{
                background: {accent_gradient};
                border: none;
                border-radius: 12px;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton#btn_download:hover {{
                background: {accent_gradient_hover};
            }}
            QPushButton#btn_download:pressed {{
                background: {accent_gradient_pressed};
            }}
            QPushButton#btn_later {{
                background-color: {btn_recal_bg};
                color: {btn_recal_text};
                border: {btn_recal_border};
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton#btn_later:hover {{
                background-color: {btn_recal_hover};
                border-color: {btn_recal_hover_border};
            }}
            QPushButton#btn_later:pressed {{
                background-color: {btn_recal_pressed};
            }}
            QPushButton#btn_settings {{
                background-color: {btn_settings_bg};
                color: {btn_settings_text};
                border: {btn_settings_border};
                border-radius: 12px;
                font-size: 18px;
            }}
            QPushButton#btn_settings:hover {{
                background-color: {btn_settings_hover_bg};
                color: {btn_settings_hover_text};
                border-color: {btn_settings_hover_border};
            }}
            QPushButton#btn_settings:pressed {{
                background-color: {btn_settings_pressed};
            }}
            QPushButton#btn_kofi {{
                background-color: {kofi_bg};
                border: {kofi_border};
                border-radius: 20px;
            }}
            QPushButton#btn_kofi:hover {{
                background-color: {kofi_hover_bg};
            }}
            QLabel#kofi_circle {{
                background-color: {kofi_circle_bg};
                color: {kofi_circle_color};
                font-size: 14px;
                border-radius: 14px;
            }}
            QLabel#kofi_text {{
                color: {text_primary};
                font-weight: bold;
                font-size: 13px;
                background: transparent;
            }}
            QLabel#kofi_arrow {{
                color: {kofi_arrow_color};
                font-size: 18px;
                background: transparent;
            }}
            QSlider::groove:horizontal {{
                height: 4px;
                background: {slider_groove};
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {accent};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {slider_handle};
                width: 12px;
                height: 12px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 6px;
                border: 1px solid #D4D4D8;
            }}
            QProgressBar {{
                border: none;
                height: 16px;
                background-color: {slider_groove};
                border-radius: 8px;
                text-align: center;
                color: transparent;
            }}
            QProgressBar::chunk {{
                background: {progress_chunk};
                border-radius: 8px;
            }}
            QCheckBox {{
                spacing: 8px;
                font-size: 13px;
                color: {chk_color};
                background-color: transparent;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: {chk_indicator_border};
                border-radius: 4px;
                background-color: {chk_indicator_bg};
            }}
            QCheckBox::indicator:hover {{
                border-color: #14B8A6;
            }}
            QCheckBox::indicator:checked {{
                background-color: #14B8A6;
                border: {chk_indicator_checked_border};
                image: url(ui/check.png);
            }}
            QLabel#preview_label {{
                border: {preview_border};
                border-radius: 8px;
                background-color: {preview_bg};
                color: {preview_text};
                font-size: 12px;
            }}
            QComboBox {{
                background-color: {combo_bg};
                color: {text_primary};
                border: {combo_border};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 14px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {combo_view_bg};
                color: {text_primary};
                selection-background-color: {combo_selection_bg};
                selection-color: {combo_selection_text};
                border: {combo_view_border};
            }}
            QToolTip {{
                border: 0px;
                background-color: {tooltip_bg};
                color: {tooltip_color};
                border-radius: 6px;
                padding: 6px 10px;
                font-family: 'Segoe UI', -apple-system, sans-serif;
                font-size: 11px;
            }}
            QLabel#lbl_metric_unit {{
                font-size: 13px;
                color: {text_secondary};
                background: transparent;
                font-weight: normal;
                margin-bottom: 2px;
            }}
            QLabel#lbl_credits, QLabel#lbl_version {{
                font-size: 11px;
                color: {text_copyright};
                background: transparent;
            }}
        """

    def update_theme(self):
        qss = self.get_qss(self.dark_theme_state)
        self.setStyleSheet(qss)
        self.update_title_bar_theme(self.dark_theme_state)
        if hasattr(self, 'spark_widget'):
            self.spark_widget.set_dark_mode(self.dark_theme_state)
        if hasattr(self, 'recal_icon'):
            self.recal_icon.set_dark_mode(self.dark_theme_state)
        if hasattr(self, 'scan_icon'):
            self.scan_icon.set_dark_mode(self.dark_theme_state)
        if hasattr(self, 'bpm_pulse'):
            self.bpm_pulse.set_dark_mode(self.dark_theme_state)
        if hasattr(self, 'progress_bar'):
            self.progress_bar.set_dark_mode(self.dark_theme_state)
        if hasattr(self, 'progress_overlay'):
            self.progress_overlay.set_dark_mode(self.dark_theme_state)
        if self.active_dialog:
            self.active_dialog.setStyleSheet(qss)

    def update_title_bar_theme(self, is_dark: bool):
        self._set_title_bar_theme_for_hwnd(int(self.winId()), is_dark)
        if self.active_dialog:
            self._set_title_bar_theme_for_hwnd(int(self.active_dialog.winId()), is_dark)

    def _set_title_bar_theme_for_hwnd(self, hwnd, is_dark: bool):
        try:
            import ctypes
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            state = ctypes.c_int(1 if is_dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(state), ctypes.sizeof(state)
            )
        except Exception as e:
            print(f"Failed to set window title bar theme for hwnd {hwnd}: {e}")

    def init_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)
        
        # Header Row (Title and Settings Button)
        layout_header = QHBoxLayout()
        layout_header.setContentsMargins(-16, 0, 0, 0)
        layout_header.setSpacing(2)
        
        # Sparkles Widget absolute positioning
        self.spark_widget = SparkWidget(self)
        self.spark_widget.move(4, 16)
        self.spark_widget.raise_()
        # layout_header.addWidget(self.spark_widget, 0, Qt.AlignmentFlag.AlignTop)
        
        # QVBox for brand title and subtitle
        layout_title_text = QVBoxLayout()
        layout_title_text.setSpacing(0)
        
        self.lbl_title = QLabel("Blinker")
        self.lbl_title.setObjectName("lbl_title")
        
        self.lbl_subtitle = QLabel("Your Eye Guardian")
        self.lbl_subtitle.setObjectName("lbl_subtitle")
        
        layout_title_text.addWidget(self.lbl_title)
        layout_title_text.addWidget(self.lbl_subtitle)
        layout_header.addLayout(layout_title_text)
        
        layout_header.addStretch()
        
        # Settings Button in a card look
        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setObjectName("btn_settings")
        self.btn_settings.setFixedSize(40, 40)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.clicked.connect(self.open_settings_dialog)
        layout_header.addWidget(self.btn_settings)
        main_layout.addLayout(layout_header)
        
        # Card 1: Main Controls
        card_buttons = QFrame()
        card_buttons.setObjectName("card")
        layout_buttons = QHBoxLayout(card_buttons)
        layout_buttons.setContentsMargins(16, 16, 16, 16)
        layout_buttons.setSpacing(16)
        
        # Toggle tracking button with custom inner layout
        self.btn_toggle = QPushButton()
        self.btn_toggle.setObjectName("btn_toggle")
        self.btn_toggle.setFixedHeight(48)
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle_tracking)
        
        toggle_layout = QHBoxLayout(self.btn_toggle)
        toggle_layout.setContentsMargins(16, 4, 16, 4)
        toggle_layout.setSpacing(8)
        
        self.lbl_toggle_icon = ToggleButtonIconWidget()
        
        self.lbl_toggle_text = QLabel()
        self.lbl_toggle_text.setObjectName("toggle_text")
        self.lbl_toggle_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        toggle_layout.addStretch()
        toggle_layout.addWidget(self.lbl_toggle_icon)
        toggle_layout.addWidget(self.lbl_toggle_text)
        toggle_layout.addStretch()
        
        layout_buttons.addWidget(self.btn_toggle, 1)
        
        # Recalibrate button
        self.btn_recalibrate = QPushButton()
        self.btn_recalibrate.setObjectName("btn_recalibrate")
        self.btn_recalibrate.setEnabled(True)
        self.btn_recalibrate.setFixedHeight(48)
        self.btn_recalibrate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_recalibrate.clicked.connect(self.recalibrate)
        
        recal_layout = QHBoxLayout(self.btn_recalibrate)
        recal_layout.setContentsMargins(16, 4, 16, 4)
        recal_layout.setSpacing(8)
        
        self.recal_icon = TargetIconWidget()
        
        self.lbl_recal_text = QLabel()
        self.lbl_recal_text.setObjectName("recal_text")
        self.lbl_recal_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        recal_layout.addStretch()
        recal_layout.addWidget(self.recal_icon)
        recal_layout.addWidget(self.lbl_recal_text)
        recal_layout.addStretch()
        
        layout_buttons.addWidget(self.btn_recalibrate, 1)
        
        main_layout.addWidget(card_buttons)
        
        # Card 2: Status Panel & Metrics
        card_status = QFrame()
        card_status.setObjectName("card")
        layout_status = QVBoxLayout(card_status)
        layout_status.setContentsMargins(16, 16, 16, 16)
        layout_status.setSpacing(14)
        
        # Status LED Row
        layout_status_row = QHBoxLayout()
        layout_status_row.setSpacing(12)
        layout_status_row.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.status_led = QLabel()
        self.status_led.setFixedSize(14, 14)
        self.set_status_led("#52525B")  # Gray initially
        layout_status_row.addWidget(self.status_led)
        
        # Stacked status text
        layout_status_text = QVBoxLayout()
        layout_status_text.setSpacing(2)
        self.lbl_status_title = QLabel("Tracking stopped")
        self.lbl_status_title.setObjectName("lbl_status_title")
        self.lbl_status_sub = QLabel("Ready")
        self.lbl_status_sub.setObjectName("lbl_status_sub")
        layout_status_text.addWidget(self.lbl_status_title)
        layout_status_text.addWidget(self.lbl_status_sub)
        layout_status_row.addLayout(layout_status_text)
        
        layout_status_row.addStretch()
        
        # Scan indicator card icon
        self.scan_icon = ScanIconWidget()
        layout_status_row.addWidget(self.scan_icon)
        
        layout_status.addLayout(layout_status_row)
        
        # Capsule Progress Bar
        self.progress_bar = CustomProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(16)
        layout_status.addWidget(self.progress_bar)
        
        # Horizontal Separator line
        sep_horiz = QFrame()
        sep_horiz.setFrameShape(QFrame.Shape.HLine)
        sep_horiz.setObjectName("sep_horiz")
        layout_status.addWidget(sep_horiz)
        
        # Two-column Metrics Row
        layout_metrics = QHBoxLayout()
        layout_metrics.setSpacing(8)
        
        # Left column (EAR)
        layout_ear_col = QVBoxLayout()
        layout_ear_col.setSpacing(4)
        
        layout_ear_title_row = QHBoxLayout()
        layout_ear_title_row.setSpacing(4)
        self.lbl_ear_title = QLabel("Current EAR index")
        self.lbl_ear_title.setObjectName("lbl_metric_title")
        self.lbl_ear_info = QLabel("ⓘ")
        self.lbl_ear_info.setObjectName("info_icon")
        self.lbl_ear_info.setCursor(Qt.CursorShape.PointingHandCursor)
        layout_ear_title_row.addWidget(self.lbl_ear_title)
        layout_ear_title_row.addWidget(self.lbl_ear_info)
        layout_ear_title_row.addStretch()
        layout_ear_col.addLayout(layout_ear_title_row)
        
        layout_ear_val_row = QHBoxLayout()
        layout_ear_val_row.setSpacing(6)
        self.lbl_ear_val = QLabel("---")
        self.lbl_ear_val.setObjectName("lbl_metric_val")
        self.lbl_ear_val.setStyleSheet("font-weight: bold; font-size: 24px; color: #71717A; background: transparent;")
        self.lbl_ear_arrow = QLabel("↕")
        self.lbl_ear_arrow.setObjectName("ear_arrow")
        layout_ear_val_row.addWidget(self.lbl_ear_val)
        layout_ear_val_row.addWidget(self.lbl_ear_arrow)
        layout_ear_val_row.addStretch()
        layout_ear_col.addLayout(layout_ear_val_row)
        
        layout_metrics.addLayout(layout_ear_col, 1)
        
        # Vertical Separator
        self.vline = QFrame()
        self.vline.setFrameShape(QFrame.Shape.VLine)
        self.vline.setObjectName("metric_sep")
        layout_metrics.addWidget(self.vline)
        
        # Right column (BPM)
        layout_bpm_col = QVBoxLayout()
        layout_bpm_col.setSpacing(4)
        
        layout_bpm_title_row = QHBoxLayout()
        layout_bpm_title_row.setSpacing(4)
        self.lbl_bpm_title = QLabel("Average frequency")
        self.lbl_bpm_title.setObjectName("lbl_metric_title")
        self.lbl_bpm_info = QLabel("ⓘ")
        self.lbl_bpm_info.setObjectName("info_icon")
        self.lbl_bpm_info.setCursor(Qt.CursorShape.PointingHandCursor)
        layout_bpm_title_row.addWidget(self.lbl_bpm_title)
        layout_bpm_title_row.addWidget(self.lbl_bpm_info)
        layout_bpm_title_row.addStretch()
        layout_bpm_col.addLayout(layout_bpm_title_row)
        
        layout_bpm_val_row = QHBoxLayout()
        layout_bpm_val_row.setSpacing(6)
        self.lbl_bpm_val = QLabel("---")
        self.lbl_bpm_val.setObjectName("lbl_metric_val_bpm")
        self.lbl_bpm_val.setStyleSheet("font-weight: bold; font-size: 24px; color: #71717A; background: transparent;")
        self.lbl_bpm_unit = QLabel("BPM")
        self.lbl_bpm_unit.setObjectName("lbl_metric_unit")
        self.bpm_pulse = PulseIconWidget()
        layout_bpm_val_row.addWidget(self.lbl_bpm_val)
        layout_bpm_val_row.addWidget(self.lbl_bpm_unit)
        layout_bpm_val_row.addWidget(self.bpm_pulse)
        layout_bpm_val_row.addStretch()
        layout_bpm_col.addLayout(layout_bpm_val_row)
        
        layout_metrics.addLayout(layout_bpm_col, 1)
        
        layout_status.addLayout(layout_metrics)
        main_layout.addWidget(card_status)
        
        # Calibration instruction (large centered helper text)
        self.lbl_calibration = QLabel("")
        self.lbl_calibration.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_calibration.setObjectName("lbl_calibration")
        
        # Verification dots frame
        self.frame_verification = QFrame()
        self.frame_verification.setStyleSheet("background: transparent;")
        layout_verification = QHBoxLayout(self.frame_verification)
        layout_verification.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_verification.setSpacing(10)
        
        self.verification_dots = []
        for _ in range(3):
            dot = QLabel()
            dot.setFixedSize(16, 16)
            dot.setStyleSheet(self.get_inactive_dot_style())
            layout_verification.addWidget(dot)
            self.verification_dots.append(dot)
            
        self.frame_verification.hide()
        
        # Camera preview
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(320, 240)
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_label.setObjectName("preview_label")
        self.preview_label.setText("Прев'ю вимкнено")
        self.preview_label.hide()
        main_layout.addWidget(self.preview_label)
        
        # Invisible spacer widget to keep controls at the top when preview is hidden
        self.spacer_widget = QWidget()
        self.spacer_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.spacer_widget.show()
        main_layout.addWidget(self.spacer_widget)
        
        # Support Author (Ko-fi) button
        self.btn_kofi = QPushButton()
        self.btn_kofi.setObjectName("btn_kofi")
        self.btn_kofi.setFixedHeight(44)
        self.btn_kofi.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_kofi.clicked.connect(self.open_kofi)
        
        kofi_layout = QHBoxLayout(self.btn_kofi)
        kofi_layout.setContentsMargins(16, 4, 16, 4)
        kofi_layout.setSpacing(8)
        
        self.lbl_kofi_text = QLabel("Buy me a coffee")
        self.lbl_kofi_text.setObjectName("kofi_text")
        self.lbl_kofi_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_kofi_arrow = QLabel("›")
        lbl_kofi_arrow.setObjectName("kofi_arrow")
        lbl_kofi_arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        kofi_layout.addSpacing(12)  # balance arrow on the right
        kofi_layout.addStretch()
        kofi_layout.addWidget(self.lbl_kofi_text)
        kofi_layout.addStretch()
        kofi_layout.addWidget(lbl_kofi_arrow)
        
        main_layout.addWidget(self.btn_kofi)
        
        # Static copyright and version credits
        layout_credits = QHBoxLayout()
        
        lbl_version = QLabel(f"v{self.APP_VERSION}")
        lbl_version.setObjectName("lbl_version")
        layout_credits.addWidget(lbl_version)
        
        layout_credits.addStretch()
        
        lbl_credits = QLabel("© Made by Kufo 2026")
        lbl_credits.setObjectName("lbl_credits")
        lbl_credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_credits.addWidget(lbl_credits)
        
        layout_credits.addStretch()
        
        # Transparent spacer widget of equal size to align copyright precisely at center
        lbl_spacer = QLabel(f"v{self.APP_VERSION}")
        lbl_spacer.setStyleSheet("color: transparent; background: transparent;")
        layout_credits.addWidget(lbl_spacer)
        
        main_layout.addLayout(layout_credits)
        
        self.update_theme()
        self.lock_optimal_size()

    def lock_optimal_size(self):
        if self.preview_enabled_state:
            self.setFixedSize(446, 720)
        else:
            self.setFixedSize(446, 529)

    def set_status_led(self, color_hex):
        """Sets the background color of the status indicator circle."""
        self.status_led.setStyleSheet(f"""
            background-color: {color_hex};
            border-radius: 7px;
        """)

    def start_session(self):
        self.session_active_duration = 0.0
        self.last_active_time = None
        self.total_blinks = 0
        self.session_active = True
        print("Tracking session started.")

    def open_kofi(self):
        webbrowser.open("https://ko-fi.com/kufo18")

    def get_translation(self, key):
        return self.lang_manager.translate(key)

    def update_toggle_button_state(self):
        if not self.tracking_active:
            self.lbl_toggle_text.setText(self.get_translation("btn_start"))
            self.lbl_toggle_icon.set_mode(False)
        else:
            self.lbl_toggle_text.setText(self.get_translation("btn_stop"))
            self.lbl_toggle_icon.set_mode(True)

    def set_status_from_text(self, text):
        found_key = None
        for key, val in LANGUAGES[self.current_language].items():
            if val == text:
                found_key = key
                break
        
        sub = ""
        if found_key:
            sub = self.get_translation(found_key + "_sub")
        elif text.startswith("Помилка") or text.startswith("Error") or text.startswith("Error"):
            sub = self.get_translation("error_sub")
            
        self.lbl_status_title.setText(text)
        self.lbl_status_sub.setText(sub)

    def retranslate_ui(self):
        self.setWindowTitle(self.get_translation("title"))
        self.lbl_subtitle.setText(self.get_translation("subtitle"))
        self.lbl_recal_text.setText(self.get_translation("btn_recalibrate"))
        
        self.lbl_ear_info.setToolTip(self.get_translation("ear_tooltip"))
        self.lbl_bpm_info.setToolTip(self.get_translation("bpm_tooltip"))
        self.lbl_ear_title.setText(self.get_translation("lbl_ear_title"))
        self.lbl_bpm_title.setText(self.get_translation("lbl_bpm_title"))
            
        self.update_toggle_button_state()
        self.update_status_text()
        
        # Overlay Window Text update
        self.overlay_window.label.setText(self.get_translation("overlay_text"))
        
        # Ko-fi button text update
        self.lbl_kofi_text.setText(self.get_translation("support_kofi"))

        # Tray actions translation
        if hasattr(self, 'action_show'):
            self.action_show.setText(self.get_translation("tray_show"))
        if hasattr(self, 'action_exit'):
            self.action_exit.setText(self.get_translation("tray_exit"))

    def update_status_text(self):
        if not self.tracking_active:
            if self.thread.calibrated:
                self.set_status_from_text(self.get_translation("status_config_loaded"))
                self.set_status_led("#3B82F6") # Blue
            else:
                self.set_status_from_text(self.get_translation("status_calib_req"))
                self.set_status_led("#EF4444") # Red
            if hasattr(self, 'scan_icon'):
                self.scan_icon.hide()
        else:
            if not self.thread.calibrated:
                if hasattr(self, 'scan_icon'):
                    self.scan_icon.hide()
            else:
                if self.face_in_view:
                    if hasattr(self, 'scan_icon'):
                        self.scan_icon.show()
                    if self.night_boost_on:
                        self.set_status_from_text(self.get_translation("status_face_night"))
                        self.set_status_led("#3B82F6") # Blue
                    else:
                        self.set_status_from_text(self.get_translation("status_face_ok"))
                        self.set_status_led("#10B981") # Green
                else:
                    if hasattr(self, 'scan_icon'):
                        self.scan_icon.hide()
                    self.set_status_from_text(self.get_translation("status_face_lost"))
                    self.set_status_led("#EF4444") # Red

    def update_active_duration(self):
        if not hasattr(self, 'session_active') or not self.session_active:
            return
            
        if self.face_in_view:
            current_time = time.time()
            if self.last_active_time is not None:
                dt = current_time - self.last_active_time
                self.session_active_duration += dt
            self.last_active_time = current_time
        else:
            self.last_active_time = None

    def save_session_to_history(self):
        if not hasattr(self, 'session_active') or not self.session_active:
            return
            
        self.update_active_duration()
        self.session_active = False
        duration = self.session_active_duration
        
        # Only save if there was tracking duration > 0
        if duration <= 0:
            return
            
        bpm = (self.total_blinks / duration) * 60
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        session_record = {
            "timestamp": timestamp_str,
            "duration_seconds": round(duration, 1),
            "total_blinks": self.total_blinks,
            "average_bpm": round(bpm, 1)
        }
        
        import os
        import json
        history_file = "history.json"
        history_data = []
        
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history_data = json.load(f)
                    if not isinstance(history_data, list):
                        history_data = []
            except Exception as e:
                print(f"Error reading history.json: {e}")
                history_data = []
                
        history_data.append(session_record)
        
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history_data, f, indent=4, ensure_ascii=False)
            print(f"Session data saved to {history_file}: {session_record}")
        except Exception as e:
            print(f"Error writing to history.json: {e}")

    def toggle_tracking(self):
        if not self.tracking_active:
            # Start
            self.tracking_active = True
            self.face_in_view = False
            self.update_toggle_button_state()
            self.btn_recalibrate.setEnabled(True)
            self.set_status_from_text(self.get_translation("status_starting"))
            self.set_status_led("#F59E0B") # Orange (starting)
            
            self.lbl_ear_val.setStyleSheet("")
            
            self.thread.set_send_preview(self.preview_enabled_state)
            if not self.thread.calibrated:
                self.thread.recalibrate()
            self.thread.start()
            
            if self.thread.calibrated:
                self.start_session()
        else:
            # Stop
            self.save_session_to_history()
            self.tracking_active = False
            self.face_in_view = False
            self.update_toggle_button_state()
            self.set_status_from_text(self.get_translation("status_stopped"))
            self.set_status_led("#52525B")  # Gray
            self.lbl_calibration.setText("")
            self.lbl_ear_val.setText("---")
            self.lbl_ear_val.setStyleSheet("font-weight: bold; font-size: 24px; color: #71717A; background: transparent;")
            self.lbl_bpm_val.setText("---")
            self.lbl_bpm_val.setStyleSheet("font-weight: bold; font-size: 24px; color: #71717A; background: transparent;")
            self.progress_bar.setValue(0)
            
            self.thread.stop()
            self.overlay_window.hide()
            self.progress_overlay.hide()
            if hasattr(self, 'calibration_overlay') and self.calibration_overlay:
                self.calibration_overlay.close()
                self.calibration_overlay = None
            self.frame_verification.hide()
            self.time_since_last_blink = 0.0
            self.night_boost_on = False
            
            if self.preview_enabled_state:
                self.preview_label.setText(self.get_translation("preview_disabled"))

    def recalibrate(self):
        self.lock_optimal_size()
        
        # Stop any warnings
        self.time_since_last_blink = 0.0
        self.overlay_window.hide()
        self.progress_overlay.hide()
        
        # Close old overlay if exists
        if hasattr(self, 'calibration_overlay') and self.calibration_overlay:
            self.calibration_overlay.close()
            self.calibration_overlay = None
            
        # Temporarily set calibrated to False during calibration process
        self.thread.calibrated = False
        
        # Set status to Calibrating...
        self.set_status_from_text(self.get_translation("status_calibrating"))
        self.set_status_led("#F59E0B")  # Orange
        self.lbl_calibration.setText("")
        
        # Instantiate the new CalibrationOverlay
        self.calibration_overlay = CalibrationOverlay(self)
        
        if not self.tracking_active:
            self.toggle_tracking()
        else:
            self.save_session_to_history()
            self.start_session()

    # Thread slots
    @pyqtSlot(str)
    def on_calibration_message(self, message):
        self.lbl_calibration.setText(message)
        if message:
            self.set_status_led("#F59E0B")  # Orange during calibration warning

    @pyqtSlot()
    def on_blink_detected(self):
        self.time_since_last_blink = 0.0
        self.overlay_window.hide()
        if hasattr(self, 'session_active') and self.session_active:
            self.total_blinks += 1

    @pyqtSlot(float)
    def on_ear_updated(self, ear_value):
        if self.tracking_active:
            self.lbl_ear_val.setText(f"{ear_value:.3f}")

    @pyqtSlot(bool)
    def on_face_detected(self, face_found):
        self.face_in_view = face_found
        self.update_status_text()

    @pyqtSlot(bool)
    def on_night_boost_active(self, active):
        self.night_boost_on = active
        self.update_status_text()

    @pyqtSlot(QImage)
    def on_frame_updated(self, q_image):
        if self.preview_enabled_state:
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(
                self.preview_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled_pixmap)

    @pyqtSlot(str)
    def on_status_message(self, message):
        print(message)
        is_error = message.startswith("Помилка") or message.startswith("Error")
        if not is_error:
            # Don't overwrite face warning status
            if not self.lbl_status_title.text().startswith("Обличчя") and not self.lbl_status_title.text().startswith("Face"):
                self.set_status_from_text(message)
        else:
            self.set_status_from_text(message)
            self.set_status_led("#EF4444")  # Red
            if self.tracking_active:
                self.toggle_tracking()

    def on_timer_tick(self):
        if not self.tracking_active or not getattr(self.thread, 'camera_active', False):
            return
            
        # Update BPM
        if hasattr(self, 'session_active') and self.session_active:
            self.update_active_duration()
            elapsed = self.session_active_duration
            if elapsed >= 10.0:
                bpm = (self.total_blinks / elapsed) * 60
                self.lbl_bpm_val.setText(f"{bpm:.1f}")
                
                # Dynamic colors based on BPM
                if bpm > 12:
                    self.lbl_bpm_val.setStyleSheet("font-weight: bold; font-size: 24px; color: #10B981; background: transparent;")
                elif 8 <= bpm <= 12:
                    self.lbl_bpm_val.setStyleSheet("font-weight: bold; font-size: 24px; color: #F59E0B; background: transparent;")
                else:
                    self.lbl_bpm_val.setStyleSheet("font-weight: bold; font-size: 24px; color: #EF4444; background: transparent;")
            else:
                self.lbl_bpm_val.setText(self.get_translation("bpm_waiting"))
                self.lbl_bpm_val.setStyleSheet("font-weight: bold; font-size: 24px; color: #71717A; background: transparent;")
        else:
            self.lbl_bpm_val.setText("---")
            self.lbl_bpm_val.setStyleSheet("font-weight: bold; font-size: 24px; color: #71717A; background: transparent;")
            
        # Normal tracking timer logic
        if self.face_in_view:
            self.time_since_last_blink += 0.1
            
            # Show overlay if timeout reached
            if self.time_since_last_blink >= self.timeout_duration:
                self.overlay_window.show()
                
            # Update progress bar
            progress_ratio = self.time_since_last_blink / self.timeout_duration
            progress_pct = int(progress_ratio * 100)
            if 0 < progress_pct < 3:
                progress_pct = 3
            self.progress_bar.setValue(min(progress_pct, 100))
            
            # Dynamic colors for overlay bar
            if progress_pct < 50:
                color = "#10B981"
            elif progress_pct < 80:
                color = "#F59E0B"
            else:
                color = "#EF4444"
                
            # Update and show top of screen floating progress bar
            self.progress_overlay.set_progress(progress_ratio, color)
            self.progress_overlay.show()
        else:
            self.progress_overlay.hide()

    def closeEvent(self, event):
        if hasattr(self, 'force_exit') and self.force_exit:
            # Shutdown completely
            self.save_session_to_history()
            self.thread.stop()
            self.overlay_window.close()
            self.progress_overlay.close()
            if hasattr(self, 'calibration_overlay') and self.calibration_overlay:
                self.calibration_overlay.close()
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()
            event.accept()
        elif self.tray_enabled_state:
            # Minimize to tray
            event.ignore()
            self.hide()
            # Show bubble notification
            title = self.get_translation("tray_bubble_title")
            msg = self.get_translation("tray_bubble_msg")
            if hasattr(self, 'tray_icon'):
                self.tray_icon.showMessage(
                    title,
                    msg,
                    QSystemTrayIcon.MessageIcon.Information,
                    3000
                )
        else:
            # Shutdown completely
            self.save_session_to_history()
            self.thread.stop()
            self.overlay_window.close()
            self.progress_overlay.close()
            if hasattr(self, 'calibration_overlay') and self.calibration_overlay:
                self.calibration_overlay.close()
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()
            event.accept()

    def save_config(self):
        config_data = {
            "threshold": self.thread.threshold,
            "avg_open_ear": getattr(self.thread, "avg_open_ear", 0.3),
            "min_closed_ear": getattr(self.thread, "min_closed_ear", 0.15),
            "timeout": self.timeout_duration,
            "show_camera": self.preview_enabled_state,
            "language": self.current_language,
            "minimize_to_tray": self.tray_enabled_state,
            "autostart": self.autostart_enabled_state,
            "theme": "dark" if self.dark_theme_state else "light"
        }
        try:
            import json
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
            print("Configuration saved to config.json")
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def load_config(self):
        import os
        import json
        if os.path.exists("config.json"):
            try:
                self.is_loading = True
                with open("config.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Load values
                threshold = data.get("threshold", 0.2)
                self.timeout_duration = data.get("timeout", 12.0)
                show_camera = data.get("show_camera", False)
                self.current_language = data.get("language", "en")
                self.lang_manager.current_language = self.current_language
                minimize_to_tray = data.get("minimize_to_tray", False)
                autostart = data.get("autostart", False)
                theme = data.get("theme", "light")
                
                # Set thread values
                self.thread.threshold = threshold
                self.thread.calibrated = True
                self.thread.avg_open_ear = data.get("avg_open_ear", 0.3)
                self.thread.min_closed_ear = data.get("min_closed_ear", 0.15)
                self.thread.language = self.current_language
                
                # Update UI States
                self.preview_enabled_state = show_camera
                self.tray_enabled_state = minimize_to_tray
                self.autostart_enabled_state = autostart
                self.dark_theme_state = (theme == "dark")
                
                # Update UI visibility
                if self.preview_enabled_state:
                    self.preview_label.show()
                    self.spacer_widget.hide()
                else:
                    self.preview_label.hide()
                    self.spacer_widget.show()
                
                self.btn_toggle.setEnabled(True)
                
                self.update_theme()
                self.retranslate_ui()
                self.set_status_from_text(self.get_translation("status_config_loaded"))
                self.set_status_led("#3B82F6") # Blue
                self.is_loading = False
                self.lock_optimal_size()
                return True
            except Exception as e:
                print(f"Error loading configuration: {e}")
                self.is_loading = False
        
        # If no config or load failed
        self.current_language = "en"
        self.lang_manager.current_language = "en"
        self.thread.language = "en"
        self.preview_enabled_state = False
        self.tray_enabled_state = False
        self.autostart_enabled_state = False
        self.dark_theme_state = False
        
        self.preview_label.hide()
        self.spacer_widget.show()
        
        self.update_theme()
        self.retranslate_ui()
        
        self.btn_toggle.setEnabled(False)
        self.set_status_from_text(self.get_translation("status_calib_req"))
        self.set_status_led("#EF4444") # Red
        self.lock_optimal_size()
        return False

    @pyqtSlot()
    def on_calibration_finished(self):
        self.frame_verification.hide()
        self.btn_toggle.setEnabled(True)
        self.set_status_from_text(self.get_translation("status_calib_ok"))
        self.set_status_led("#10B981") # Green
        self.save_config()
        self.lock_optimal_size()
        self.start_session()

    @pyqtSlot(int)
    def on_calibration_stage_changed(self, stage):
        if stage == 2:
            self.frame_verification.show()
            for dot in self.verification_dots:
                dot.setStyleSheet(self.get_inactive_dot_style())
            self.lock_optimal_size()

    @pyqtSlot(int)
    def on_verification_blink(self, count):
        for i in range(3):
            if i < count:
                self.verification_dots[i].setStyleSheet("background-color: #10B981; border-radius: 8px;")
            else:
                self.verification_dots[i].setStyleSheet(self.get_inactive_dot_style())

    def change_language_from_dialog(self, index):
        if index == 0:
            lang = "en"
        elif index == 1:
            lang = "uk"
        else:
            lang = "es"
        self.current_language = lang
        self.lang_manager.current_language = lang
        self.thread.language = lang
        self.save_config()

    def set_preview_enabled_from_dialog(self, enabled):
        self.preview_enabled_state = enabled
        self.thread.set_send_preview(enabled)
        if enabled:
            self.preview_label.show()
            self.spacer_widget.hide()
            if not self.tracking_active:
                self.preview_label.setText(self.get_translation("preview_waiting"))
        else:
            self.preview_label.hide()
            self.spacer_widget.show()
        self.lock_optimal_size()
        self.save_config()

    def set_tray_enabled_from_dialog(self, enabled):
        self.tray_enabled_state = enabled
        self.save_config()

    def set_autostart_enabled_from_dialog(self, enabled):
        self.autostart_enabled_state = enabled
        self.set_windows_autostart(enabled)
        self.save_config()

    def set_dark_theme_from_dialog(self, enabled):
        self.dark_theme_state = enabled
        self.update_theme()
        self.save_config()

    def open_settings_dialog(self):
        self.active_dialog = SettingsDialog(self)
        self.active_dialog.exec()
        self.active_dialog = None
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def show_update_dialog(self, new_version):
        dialog = UpdateDialog(self, new_version)
        dialog.exec()

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png"))
        
        self.tray_menu = QMenu(self)
        
        self.action_show = QAction(self)
        self.action_show.triggered.connect(self.show_normal)
        self.tray_menu.addAction(self.action_show)
        
        self.tray_menu.addSeparator()
        
        self.action_exit = QAction(self)
        self.action_exit.triggered.connect(self.exit_app)
        self.tray_menu.addAction(self.action_exit)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_normal()

    def show_normal(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def exit_app(self):
        self.force_exit = True
        self.close()
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def get_app_command_line(self):
        if sys.argv[0].endswith(".exe") or getattr(sys, 'frozen', False):
            exe_path = os.path.abspath(sys.argv[0])
            return f'"{exe_path}" --minimized'
        else:
            python_exe = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            return f'"{python_exe}" "{script_path}" --minimized'

    def set_windows_autostart(self, enabled: bool):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
        except Exception as e:
            print(f"Error opening Windows registry: {e}")
            return
            
        try:
            if enabled:
                cmd = self.get_app_command_line()
                winreg.SetValueEx(key, "Blinker", 0, winreg.REG_SZ, cmd)
                print(f"Blinker autostart parameter set: {cmd}")
            else:
                try:
                    winreg.DeleteValue(key, "Blinker")
                    print("Blinker autostart parameter deleted")
                except FileNotFoundError:
                    pass
        except Exception as e:
            print(f"Error modifying Windows registry: {e}")
        finally:
            key.Close()


class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self.lang_manager = LanguageManager.get_instance()
        self.lang_manager.subscribe(self.retranslate_dialog)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.resize(350, 290)
        
        # Stylize the dialog to match the parent
        self.setStyleSheet(self.parent_window.styleSheet())
        self.parent_window._set_title_bar_theme_for_hwnd(int(self.winId()), self.parent_window.dark_theme_state)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Card container
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(12)
        
        # Language Select Row
        lang_layout = QHBoxLayout()
        self.lbl_lang = QLabel()
        self.lbl_lang.setObjectName("lbl_lang")
        lang_layout.addWidget(self.lbl_lang)
        
        lang_layout.addStretch()
        
        self.combo_lang = QComboBox()
        self.combo_lang.addItem(QIcon("ui/flag_en.png"), "English")
        self.combo_lang.addItem(QIcon("ui/flag_ua.png"), "Українська")
        self.combo_lang.addItem(QIcon("ui/flag_es.png"), "Español")
        self.combo_lang.setFixedWidth(120)
        
        current_lang = self.lang_manager.current_language
        if current_lang == "en":
            self.combo_lang.setCurrentIndex(0)
        elif current_lang == "uk":
            self.combo_lang.setCurrentIndex(1)
        else:
            self.combo_lang.setCurrentIndex(2)
            
        self.combo_lang.activated.connect(self.on_language_changed)
        lang_layout.addWidget(self.combo_lang)
        
        card_layout.addLayout(lang_layout)
        
        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("background-color: #27272A; max-height: 1px; border: none;")
        card_layout.addWidget(sep)
        
        # Checkboxes
        self.cb_autostart = QCheckBox()
        self.cb_autostart.setChecked(self.parent_window.autostart_enabled_state)
        self.cb_autostart.stateChanged.connect(self.on_autostart_toggled)
        card_layout.addWidget(self.cb_autostart)
        
        self.cb_tray = QCheckBox()
        self.cb_tray.setChecked(self.parent_window.tray_enabled_state)
        self.cb_tray.stateChanged.connect(self.on_tray_toggled)
        card_layout.addWidget(self.cb_tray)
        
        self.chk_preview = QCheckBox()
        self.chk_preview.setChecked(self.parent_window.preview_enabled_state)
        self.chk_preview.stateChanged.connect(self.on_preview_toggled)
        card_layout.addWidget(self.chk_preview)
        
        self.cb_dark_theme = QCheckBox()
        self.cb_dark_theme.setChecked(self.parent_window.dark_theme_state)
        self.cb_dark_theme.stateChanged.connect(self.on_dark_theme_toggled)
        card_layout.addWidget(self.cb_dark_theme)
        
        layout.addWidget(card)
        
        # Close Button
        self.btn_close = QPushButton()
        self.btn_close.setObjectName("btn_recalibrate") # Reuses MainWindow secondary button style
        self.btn_close.setFixedHeight(35)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.accept)
        layout.addWidget(self.btn_close)
        
        self.retranslate_dialog()
        
    def retranslate_dialog(self):
        self.setWindowTitle(self.lang_manager.translate("settings_title"))
        self.lbl_lang.setText(self.lang_manager.translate("settings_lang"))
        self.chk_preview.setText(self.lang_manager.translate("settings_preview"))
        self.cb_tray.setText(self.lang_manager.translate("settings_tray"))
        self.cb_autostart.setText(self.lang_manager.translate("settings_autostart"))
        self.cb_dark_theme.setText(self.lang_manager.translate("cb_dark_theme"))
        self.btn_close.setText(self.lang_manager.translate("settings_close"))
        
    def on_language_changed(self, index):
        QTimer.singleShot(0, lambda: self.apply_language_change(index))
        
    def apply_language_change(self, index):
        self.combo_lang.blockSignals(True)
        try:
            self.parent_window.change_language_from_dialog(index)
        finally:
            self.combo_lang.blockSignals(False)
            
    def closeEvent(self, event):
        self.lang_manager.unsubscribe(self.retranslate_dialog)
        super().closeEvent(event)

    def accept(self):
        self.lang_manager.unsubscribe(self.retranslate_dialog)
        super().accept()

    def reject(self):
        self.lang_manager.unsubscribe(self.retranslate_dialog)
        super().reject()
        
    def on_preview_toggled(self, state):
        self.parent_window.set_preview_enabled_from_dialog(state == 2)
        
    def on_tray_toggled(self, state):
        self.parent_window.set_tray_enabled_from_dialog(state == 2)
        
    def on_autostart_toggled(self, state):
        self.parent_window.set_autostart_enabled_from_dialog(state == 2)

    def on_dark_theme_toggled(self, state):
        self.parent_window.set_dark_theme_from_dialog(state == 2)
