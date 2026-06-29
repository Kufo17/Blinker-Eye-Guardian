"""
Blinker 👁️ - Desktop Eye Tracking & Overlay Application
Supports bilingual localization (English by default, Ukrainian alternative).
"""

import sys
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.overlay_window import OverlayWindow
from ui.main_window import MainWindow

def main():
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

    # Set explicit AppUserModelID for Windows taskbar icon grouping
    myappid = 'kufo.blinker.eyeguardian.1.0'
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception as e:
        print(f"Error setting AppUserModelID: {e}")

    # Initialize the PyQt6 application
    app = QApplication(sys.argv)
    app.setApplicationName("Blinker")
    
    app.setQuitOnLastWindowClosed(False)
    
    # Set global window icon
    app.setWindowIcon(QIcon("icon.png"))
    
    # Create the click-through warning overlay (initially hidden)
    overlay = OverlayWindow()
    overlay.hide()
    
    # Create the main dashboard control panel, passing the overlay window
    main_window = MainWindow(overlay)
    if "--minimized" not in sys.argv:
        main_window.show()
    
    # Run the Qt application event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
