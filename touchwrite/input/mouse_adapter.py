"""
Standard mouse input adapter for TouchWrite (reliable initial fallback).
"""

from typing import Optional
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent

from touchwrite.input.base import BaseInputAdapter, InputDeviceType
from touchwrite.config import AppConfig


class MouseInputAdapter(BaseInputAdapter):
    """
    Standard mouse fallback adapter.
    Enables drawing with left-click drag, and panning with middle-click drag.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__("Standard Mouse Fallback", InputDeviceType.MOUSE)
        self.config = config or AppConfig()
        self.is_drawing = False

    def is_available(self) -> bool:
        """Mouse input is always available on desktop Windows."""
        return True

    def handle_mouse_press(self, event: QMouseEvent) -> bool:
        if not self.canvas:
            return False

        if event.button() == Qt.MouseButton.LeftButton:
            canvas_pt = self.canvas.screen_to_canvas(event.position())
            if self.canvas.get_paper_rect().contains(canvas_pt):
                self.is_drawing = True
                self.canvas.start_stroke(canvas_pt, pressure=1.0)
                return True
        return False

    def handle_mouse_move(self, event: QMouseEvent) -> bool:
        if not self.canvas or not self.is_drawing:
            return False

        if event.buttons() & Qt.MouseButton.LeftButton:
            canvas_pt = self.canvas.screen_to_canvas(event.position())
            self.canvas.continue_stroke(canvas_pt, pressure=1.0)
            return True
        return False

    def handle_mouse_release(self, event: QMouseEvent) -> bool:
        if not self.canvas:
            return False

        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.canvas.end_stroke()
            self.is_drawing = False
            return True
        return False
