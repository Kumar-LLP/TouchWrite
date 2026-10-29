"""
Windows 11 Fluent-inspired Light and Dark UI stylesheets for TouchWrite.
"""

LIGHT_THEME = """
QMainWindow, QDialog {
    background-color: #F3F4F6;
    color: #111827;
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
    color: #374151;
    font-size: 13px;
    font-weight: 500;
}

QToolButton:hover {
    background-color: #F3F4F6;
    border-color: #D1D5DB;
}

QToolButton:checked {
    background-color: #E0E7FF;
    border: 1px solid #6366F1;
    color: #4338CA;
    font-weight: 600;
}

QToolButton:pressed {
    background-color: #C7D2FE;
}

QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    padding: 6px 14px;
    color: #1F2937;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #F9FAFB;
    border-color: #9CA3AF;
}

QPushButton:pressed {
    background-color: #F3F4F6;
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
}

QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    padding: 5px 10px;
    color: #1F2937;
    font-size: 13px;
}

QComboBox:hover {
    border-color: #9CA3AF;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
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
    color: #4B5563;
    font-size: 12px;
    padding: 4px 12px;
}

QMenuBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E5E7EB;
    color: #1F2937;
    font-size: 13px;
}

QMenuBar::item:selected {
    background-color: #F3F4F6;
    border-radius: 4px;
}

QMenu {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 20px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #F3F4F6;
}

QGroupBox {
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: 600;
    color: #374151;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
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
}

QToolButton:checked {
    background-color: #312E81;
    border: 1px solid #6366F1;
    color: #A5B4FC;
    font-weight: 600;
}

QToolButton:pressed {
    background-color: #3730A3;
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
}

QPushButton:pressed {
    background-color: #18181B;
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
}

QMenuBar::item:selected {
    background-color: #27272A;
    border-radius: 4px;
}

QMenu {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 20px;
    border-radius: 4px;
    color: #F4F4F5;
}

QMenu::item:selected {
    background-color: #27272A;
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
"""


def apply_theme(app_or_window, theme_name: str = "light") -> None:
    """Apply Fluent light or dark stylesheet."""
    if theme_name == "dark":
        app_or_window.setStyleSheet(DARK_THEME)
    else:
        app_or_window.setStyleSheet(LIGHT_THEME)
