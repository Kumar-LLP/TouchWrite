"""
Tablet and stylus input adapter for TouchWrite (Windows Ink / External Tablet fallback).
"""

from typing import Optional
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QTabletEvent

from touchwrite.input.base import BaseInputAdapter, InputDeviceType
from touchwrite.config import AppConfig


class TabletInputAdapter(BaseInputAdapter):
    """
    Adapter for Windows Ink stylus, touchscreen digitizers, and external drawing tablets.
    Directly consumes hardware pressure sensitivity and pen-tip contact.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__("Tablet / Stylus Adapter", InputDeviceType.PEN)
        self.config = config or AppConfig()
        self.is_drawing = False

    def is_available(self) -> bool:
        """Available when an active stylus, digitizer or tablet is present."""
        return True

    def handle_tablet_event(self, event: QTabletEvent) -> bool:
        if not self.canvas:
            return False

        pos = event.position()
        canvas_pt = self.canvas.screen_to_canvas(pos)
        pressure = max(0.1, min(1.5, event.pressure()))
        event_type = event.type()

        if event_type == QTabletEvent.Type.TabletPress:
            if self.canvas.get_paper_rect().contains(canvas_pt):
                self.is_drawing = True
                self.canvas.start_stroke(canvas_pt, pressure=pressure)
                event.accept()
                return True

        elif event_type == QTabletEvent.Type.TabletMove:
            if self.is_drawing:
                self.canvas.continue_stroke(canvas_pt, pressure=pressure)
                event.accept()
                return True

        elif event_type == QTabletEvent.Type.TabletRelease:
            if self.is_drawing:
                self.canvas.end_stroke()
                self.is_drawing = False
                event.accept()
                return True

        return False
