"""
TouchWrite — Finger-Based Digital Handwriting for Windows 11.
Application Entry Point.
"""

import sys
import os

# Set Windows console to UTF-8 to prevent charmap errors
if sys.platform == "win32":
    try:
        if sys.stdout:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure package root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from touchwrite.config import AppConfig
from touchwrite.ui.main_window import MainWindow


def main():
    """Main application lifecycle runner."""
    # Create Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("TouchWrite")
    app.setApplicationDisplayName("TouchWrite")
    app.setOrganizationName("TouchWrite")

    # Load configuration
    config = AppConfig()

    # Create and display main window
    window = MainWindow(config)

    # If a file path was passed as CLI argument, open it
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        window._load_from_filepath(sys.argv[1])

    window.show()

    # Execute main loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
