"""
Windows 11 Fluent-inspired Light and Dark UI stylesheets for TouchWrite.
Ensures crisp, high-contrast, black-on-white text for all menus, options, and controls.
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

LIGHT_THEME = """
QMainWindow, QDialog {
    background-color: #F3F4F6;
    color: #000000;
}

QToolBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E5E7EB;
    padding: 6px 12px;
    spacing: 8px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 10px;
    color: #111827;
    font-size: 13px;
    font-weight: 500;
}

QToolButton:hover {
    background-color: #F3F4F6;
    border-color: #D1D5DB;
    color: #000000;
}

QToolButton:checked {
    background-color: #E0E7FF;
    border: 1px solid #6366F1;
    color: #312E81;
    font-weight: 600;
}

QToolButton:pressed {
    background-color: #C7D2FE;
    color: #000000;
}

QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    padding: 6px 14px;
    color: #000000;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #F9FAFB;
    border-color: #9CA3AF;
    color: #000000;
}

QPushButton:pressed {
    background-color: #F3F4F6;
    color: #000000;
}

QPushButton:disabled {
    color: #9CA3AF;
    background-color: #F3F4F6;
    border-color: #E5E7EB;
}

QPushButton.primary {
    background-color: #2563EB;
    color: #FFFFFF;
    border: 1px solid #1D4ED8;
    font-weight: 600;
}

QPushButton.primary:hover {
    background-color: #1D4ED8;
    color: #FFFFFF;
}

QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    padding: 5px 10px;
    color: #000000;
    font-size: 13px;
    font-weight: 500;
}

QComboBox:hover {
    border-color: #9CA3AF;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #000000;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    selection-background-color: #E5E7EB;
    selection-color: #000000;
    padding: 4px;
    font-size: 13px;
}

QSlider::groove:horizontal {
    height: 4px;
    background: #E5E7EB;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #4F46E5;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #FFFFFF;
    border: 2px solid #4F46E5;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #EEF2FF;
    transform: scale(1.1);
}

QStatusBar {
    background-color: #FFFFFF;
    border-top: 1px solid #E5E7EB;
    color: #374151;
    font-size: 12px;
    padding: 4px 12px;
}

/* -------------------------------------------------------------------------
   Top Menu Bar (File, Edit, View, Tools, Help) - High Contrast Black Text
   ------------------------------------------------------------------------- */

QMenuBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E5E7EB;
    color: #000000;
    font-size: 13px;
    font-weight: 500;
}

QMenuBar::item {
    background-color: transparent;
    color: #000000;
    padding: 6px 12px;
    margin: 2px 2px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #E5E7EB;
    color: #000000;
}

QMenuBar::item:pressed {
    background-color: #D1D5DB;
    color: #000000;
}

/* -------------------------------------------------------------------------
   Menu Dropdown Popups - Pure Black Text on Clean White Background
   ------------------------------------------------------------------------- */

QMenu {
    background-color: #FFFFFF;
    color: #000000;
    border: 1px solid #D1D5DB;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    background-color: transparent;
    color: #000000;
    font-size: 13px;
    font-weight: 500;
    padding: 7px 28px 7px 20px;
    border-radius: 4px;
    margin: 1px 4px;
}

QMenu::item:selected {
    background-color: #E5E7EB;
    color: #000000;
    font-weight: 600;
}

QMenu::item:disabled {
    color: #9CA3AF;
    background-color: transparent;
}

QMenu::separator {
    height: 1px;
    background-color: #E5E7EB;
    margin: 4px 8px;
}

QGroupBox {
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: 600;
    color: #111827;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}

QLabel {
    color: #000000;
    font-size: 13px;
}

QLineEdit, QSpinBox {
    background-color: #FFFFFF;
    color: #000000;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 13px;
}

QToolTip {
    background-color: #FFFFFF;
    color: #000000;
    border: 1px solid #D1D5DB;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}
"""

DARK_THEME = """
QMainWindow, QDialog {
    background-color: #121214;
    color: #F3F4F6;
}

QToolBar {
    background-color: #18181B;
    border-bottom: 1px solid #27272A;
    padding: 6px 12px;
    spacing: 8px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 10px;
    color: #D4D4D8;
    font-size: 13px;
    font-weight: 500;
}

QToolButton:hover {
    background-color: #27272A;
    border-color: #3F3F46;
    color: #FFFFFF;
}

QToolButton:checked {
    background-color: #312E81;
    border: 1px solid #6366F1;
    color: #A5B4FC;
    font-weight: 600;
}

QToolButton:pressed {
    background-color: #3730A3;
    color: #FFFFFF;
}

QPushButton {
    background-color: #27272A;
    border: 1px solid #3F3F46;
    border-radius: 6px;
    padding: 6px 14px;
    color: #F4F4F5;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #3F3F46;
    border-color: #52525B;
    color: #FFFFFF;
}

QPushButton:pressed {
    background-color: #18181B;
    color: #FFFFFF;
}

QPushButton:disabled {
    color: #71717A;
    background-color: #18181B;
    border-color: #27272A;
}

QPushButton.primary {
    background-color: #3B82F6;
    color: #FFFFFF;
    border: 1px solid #2563EB;
    font-weight: 600;
}

QPushButton.primary:hover {
    background-color: #2563EB;
    color: #FFFFFF;
}

QComboBox {
    background-color: #27272A;
    border: 1px solid #3F3F46;
    border-radius: 6px;
    padding: 5px 10px;
    color: #F4F4F5;
    font-size: 13px;
}

QComboBox:hover {
    border-color: #52525B;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #18181B;
    color: #F4F4F5;
    border: 1px solid #3F3F46;
    border-radius: 6px;
    selection-background-color: #27272A;
    selection-color: #FFFFFF;
    padding: 4px;
    font-size: 13px;
}

QSlider::groove:horizontal {
    height: 4px;
    background: #3F3F46;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #6366F1;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #FFFFFF;
    border: 2px solid #6366F1;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #E0E7FF;
}

QStatusBar {
    background-color: #18181B;
    border-top: 1px solid #27272A;
    color: #A1A1AA;
    font-size: 12px;
    padding: 4px 12px;
}

QMenuBar {
    background-color: #18181B;
    border-bottom: 1px solid #27272A;
    color: #F4F4F5;
    font-size: 13px;
    font-weight: 500;
}

QMenuBar::item {
    background-color: transparent;
    color: #F4F4F5;
    padding: 6px 12px;
    margin: 2px 2px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #27272A;
    color: #FFFFFF;
}

QMenuBar::item:pressed {
    background-color: #3F3F46;
    color: #FFFFFF;
}

QMenu {
    background-color: #18181B;
    color: #F4F4F5;
    border: 1px solid #27272A;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    background-color: transparent;
    color: #F4F4F5;
    font-size: 13px;
    font-weight: 500;
    padding: 7px 28px 7px 20px;
    border-radius: 4px;
    margin: 1px 4px;
}

QMenu::item:selected {
    background-color: #27272A;
    color: #FFFFFF;
    font-weight: 600;
}

QMenu::item:disabled {
    color: #71717A;
    background-color: transparent;
}

QMenu::separator {
    height: 1px;
    background-color: #27272A;
    margin: 4px 8px;
}

QGroupBox {
    border: 1px solid #27272A;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: 600;
    color: #E4E4E7;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}

QLabel {
    color: #F4F4F5;
    font-size: 13px;
}

QLineEdit, QSpinBox {
    background-color: #27272A;
    color: #F4F4F5;
    border: 1px solid #3F3F46;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 13px;
}

QToolTip {
    background-color: #27272A;
    color: #F4F4F5;
    border: 1px solid #3F3F46;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}
"""


def apply_theme(app_or_window, theme_name: str = "light") -> None:
    """Apply Fluent light or dark stylesheet and matching high-contrast palette."""
    palette = QPalette()
    if theme_name == "dark":
        palette.setColor(QPalette.ColorRole.Window, QColor("#121214"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#F4F4F5"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#18181B"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#27272A"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#27272A"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#F4F4F5"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#F4F4F5"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#27272A"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#F4F4F5"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#3B82F6"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
        app_or_window.setStyleSheet(DARK_THEME)
    else:
        palette.setColor(QPalette.ColorRole.Window, QColor("#F3F4F6"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#000000"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#F9FAFB"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#000000"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#000000"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#000000"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#2563EB"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
        app_or_window.setStyleSheet(LIGHT_THEME)

    app = QApplication.instance()
    if app:
        app.setPalette(palette)
    else:
        app_or_window.setPalette(palette)
