"""
Tests for UI components, paper styles, and theme switching.
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPainter
from touchwrite.config import AppConfig, PaperStyle, ToolMode
from touchwrite.canvas.paper import PaperRenderer
from touchwrite.ui.theme import apply_theme
from touchwrite.ui.main_window import MainWindow

_app = QApplication.instance() or QApplication([])


def test_paper_rendering_modes():
    img = QImage(800, 600, QImage.Format.Format_ARGB32)
    painter = QPainter(img)
    rect = QRectF(0, 0, 800, 600)

    # Test Blank
    PaperRenderer.render(painter, rect, PaperStyle.BLANK, spacing=30, margin_x=50, dark_mode=False)
    # Test Ruled
    PaperRenderer.render(painter, rect, PaperStyle.RULED, spacing=30, margin_x=50, dark_mode=False)
    # Test Grid
    PaperRenderer.render(painter, rect, PaperStyle.GRID, spacing=30, margin_x=50, dark_mode=False)
    # Test Dark Mode Ruled
    PaperRenderer.render(painter, rect, PaperStyle.RULED, spacing=30, margin_x=50, dark_mode=True)

    painter.end()


def test_main_window_instantiation():
    config = AppConfig()
    win = MainWindow(config)
    assert win.windowTitle().startswith("TouchWrite")

    # Test tool selection
    win._set_tool(ToolMode.ERASER)
    assert win.canvas.active_tool == ToolMode.ERASER

    win._set_tool(ToolMode.PEN)
    assert win.canvas.active_tool == ToolMode.PEN

    # Test theme toggle
    theme_before = win.config.theme
    win._toggle_theme()
    assert win.config.theme != theme_before
    win._toggle_theme()
    assert win.config.theme == theme_before

    win.close()
