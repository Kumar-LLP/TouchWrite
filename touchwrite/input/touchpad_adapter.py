"""
Touchpad input adapter specifically engineered for laptop touchpads.
Provides Hold-to-Write, Direct Contact, Auto-Dwell, and Click/Tap modes with natural stroke dynamics.
"""

import time
import math
from typing import Optional
from PySide6.QtCore import QPointF, QTimer, Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent, QCursor

from touchwrite.input.base import BaseInputAdapter, InputDeviceType
from touchwrite.config import AppConfig, InputMode


class TouchpadInputAdapter(BaseInputAdapter):
    """
    Precision Touchpad adapter translating finger glides into natural handwriting strokes.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__("Precision Touchpad Adapter", InputDeviceType.TOUCHPAD)
        self.config = config or AppConfig()

        # Writing state
        self.is_trigger_held: bool = False
        self.is_writing: bool = False
        self.last_pos: Optional[QPointF] = None
        self.last_time: float = 0.0

        # Auto-Dwell timer for lifting pen on finger pauses
        self.dwell_timer = QTimer()
        self.dwell_timer.setSingleShot(True)
        self.dwell_timer.timeout.connect(self._on_dwell_timeout)

    def is_available(self) -> bool:
        """Precision touchpads are standard on modern Windows 11 laptops."""
        return True

    def _compute_pressure(self, canvas_pt: QPointF, current_time: float) -> float:
        """
        Simulate natural pen pressure based on finger glide velocity.
        Slower, deliberate finger strokes produce slightly richer ink;
        rapid flourishes produce finer lines.
        """
        if self.last_pos is None or self.last_time <= 0:
            return 1.0

        dt = max(0.001, current_time - self.last_time)
        dx = canvas_pt.x() - self.last_pos.x()
        dy = canvas_pt.y() - self.last_pos.y()
        speed = math.hypot(dx, dy) / dt  # Pixels per second

        # Map speed (0 to 1500 px/s) to pressure range (0.6 to 1.4)
        factor = max(0.0, min(1.0, speed / 1200.0))
        # Inverse: high speed -> thinner; low speed -> thicker
        pressure = 1.3 - (factor * 0.6)
        return max(0.6, min(1.4, pressure))

    # -------------------------------------------------------------------------
    # Keyboard Trigger Handling (Hold-to-Write Mode)
    # -------------------------------------------------------------------------

    def handle_key_press(self, event: QKeyEvent) -> bool:
        # Quick toggle key 'T' for Single-Finger Tablet Mode
        if not event.isAutoRepeat() and event.key() == Qt.Key.Key_T and not (event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)):
            self.config.tablet_touchpad_mode = not self.config.tablet_touchpad_mode
            if not self.config.tablet_touchpad_mode and self.is_writing and self.canvas:
                self.canvas.end_stroke()
                self.is_writing = False
            return True

        if self.config.input_mode != InputMode.HOLD_TO_WRITE:
            return False

        # Check if matching trigger key (default Spacebar)
        if not event.isAutoRepeat() and event.key() == Qt.Key.Key_Space:
            self.is_trigger_held = True
            if self.canvas and not self.is_writing:
                # Start stroke at current cursor position
                cursor_pos = self.canvas.mapFromGlobal(QCursor.pos())
                canvas_pt = self.canvas.screen_to_canvas(cursor_pos)
                if self.canvas.get_paper_rect().contains(canvas_pt):
                    self.is_writing = True
                    self.last_pos = canvas_pt
                    self.last_time = time.time()
                    self.canvas.start_stroke(canvas_pt, pressure=1.0)
            return True
        return False

    def handle_key_release(self, event: QKeyEvent) -> bool:
        if self.config.input_mode != InputMode.HOLD_TO_WRITE:
            return False

        if not event.isAutoRepeat() and event.key() == Qt.Key.Key_Space:
            self.is_trigger_held = False
            if self.is_writing and self.canvas:
                self.canvas.end_stroke()
                self.is_writing = False
                self.last_pos = None
            return True
        return False

    # -------------------------------------------------------------------------
    # Finger Movement & Inking Handling
    # -------------------------------------------------------------------------

    def handle_mouse_move(self, event: QMouseEvent) -> bool:
        if not self.canvas:
            return False

        pos = event.position()
        canvas_pt = self.canvas.screen_to_canvas(pos)
        now = time.time()
        pressure = self._compute_pressure(canvas_pt, now)

        mode = self.config.input_mode

        # Mode 0: TABLET_TOUCHPAD (Primary Single-Finger Tablet Mode)
        # Allows drawing directly with one single finger, with ultra-fast pen-up on finger lift.
        if mode == InputMode.TABLET_TOUCHPAD or (self.config.tablet_touchpad_mode and mode != InputMode.HOLD_TO_WRITE):
            # If right or middle mouse button is pressed: allow mouse navigation/panning
            if event.buttons() & (Qt.MouseButton.RightButton | Qt.MouseButton.MiddleButton):
                return False

            if self.canvas.get_paper_rect().contains(canvas_pt):
                # Jump detection: if finger was lifted and touches down elsewhere,
                # or if speed/distance indicates a new stroke (e.g. dot an 'i', cross a 't', new letter)
                if self.is_writing and self.last_pos is not None:
                    dist = math.hypot(canvas_pt.x() - self.last_pos.x(), canvas_pt.y() - self.last_pos.y())
                    dt = max(0.001, now - self.last_time)
                    if (dist > 35.0 and dt > 0.025) or (dist > 60.0):
                        self.canvas.end_stroke()
                        self.is_writing = False

                if not self.is_writing:
                    self.is_writing = True
                    self.canvas.start_stroke(canvas_pt, pressure=pressure)
                else:
                    self.canvas.continue_stroke(canvas_pt, pressure=pressure)

                self.last_pos = canvas_pt
                self.last_time = now

                # Restart ultra-fast finger-lift timer (50ms)
                timeout = max(30, min(80, self.config.finger_lift_timeout_ms))
                self.dwell_timer.start(timeout)
                return True
            else:
                if self.is_writing:
                    self.dwell_timer.stop()
                    self.canvas.end_stroke()
                    self.is_writing = False
                    self.last_pos = None
            return False

        # Mode 1: HOLD_TO_WRITE
        if mode == InputMode.HOLD_TO_WRITE:
            if self.is_trigger_held:
                if not self.is_writing:
                    if self.canvas.get_paper_rect().contains(canvas_pt):
                        self.is_writing = True
                        self.canvas.start_stroke(canvas_pt, pressure=pressure)
                else:
                    self.canvas.continue_stroke(canvas_pt, pressure=pressure)
                self.last_pos = canvas_pt
                self.last_time = now
                return True
            return False

        # Mode 2: DIRECT_CONTACT
        elif mode == InputMode.DIRECT_CONTACT:
            if self.canvas.get_paper_rect().contains(canvas_pt):
                if not self.is_writing:
                    self.is_writing = True
                    self.canvas.start_stroke(canvas_pt, pressure=pressure)
                else:
                    self.canvas.continue_stroke(canvas_pt, pressure=pressure)
                self.last_pos = canvas_pt
                self.last_time = now
                # Restart dwell timer to commit stroke when finger is lifted
                self.dwell_timer.start(self.config.dwell_timeout_ms)
                return True
            else:
                if self.is_writing:
                    self.canvas.end_stroke()
                    self.is_writing = False
            return False

        # Mode 3: AUTO_DWELL
        elif mode == InputMode.AUTO_DWELL:
            if self.canvas.get_paper_rect().contains(canvas_pt):
                if not self.is_writing:
                    self.is_writing = True
                    self.canvas.start_stroke(canvas_pt, pressure=pressure)
                else:
                    self.canvas.continue_stroke(canvas_pt, pressure=pressure)
                self.last_pos = canvas_pt
                self.last_time = now
                # Restart dwell timer
                self.dwell_timer.start(self.config.dwell_timeout_ms)
                return True
            return False

        # Mode 4: CLICK_AND_DRAG
        elif mode == InputMode.CLICK_AND_DRAG:
            if event.buttons() & Qt.MouseButton.LeftButton:
                if not self.is_writing:
                    self.is_writing = True
                    self.canvas.start_stroke(canvas_pt, pressure=pressure)
                else:
                    self.canvas.continue_stroke(canvas_pt, pressure=pressure)
                self.last_pos = canvas_pt
                self.last_time = now
                return True
            return False

        return False

    def handle_mouse_press(self, event: QMouseEvent) -> bool:
        if not self.canvas:
            return False

        if event.button() == Qt.MouseButton.LeftButton:
            canvas_pt = self.canvas.screen_to_canvas(event.position())
            if self.canvas.get_paper_rect().contains(canvas_pt):
                if self.is_writing:
                    self.canvas.end_stroke()
                self.is_writing = True
                self.last_pos = canvas_pt
                self.last_time = time.time()
                self.canvas.start_stroke(canvas_pt, pressure=1.0)
                timeout = max(30, min(80, self.config.finger_lift_timeout_ms))
                self.dwell_timer.start(timeout)
                return True
        return False

    def handle_mouse_release(self, event: QMouseEvent) -> bool:
        if not self.canvas:
            return False

        if event.button() == Qt.MouseButton.LeftButton and self.is_writing:
            self.dwell_timer.stop()
            self.canvas.end_stroke()
            self.is_writing = False
            self.last_pos = None
            return True
        return False

    def _on_dwell_timeout(self) -> None:
        """Triggered in AUTO_DWELL mode when finger pauses or lifts."""
        if self.is_writing and self.canvas:
            self.canvas.end_stroke()
            self.is_writing = False
            self.last_pos = None
