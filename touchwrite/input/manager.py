"""
Central input manager coordinating adapters, fallback detection, and telemetry.
"""

from typing import Dict, List, Optional
from PySide6.QtCore import QObject, Signal, QPointF, Qt

from touchwrite.config import AppConfig, InputMode
from touchwrite.input.base import BaseInputAdapter, InputDeviceType
from touchwrite.input.touchpad_adapter import TouchpadInputAdapter
from touchwrite.input.mouse_adapter import MouseInputAdapter
from touchwrite.input.tablet_adapter import TabletInputAdapter
from touchwrite.input.win_pointer_adapter import WinPointerAdapter


class InputManager(QObject):
    """
    Coordinates all input sources (touchpad, mouse, pen, touchscreen, native Windows pointer),
    handles input fallbacks, and notifies the UI about device status.
    """

    # Signals
    device_changed = Signal(str)           # Friendly name of active device
    mode_changed = Signal(str)             # Friendly name of active mode
    telemetry_updated = Signal(dict)       # Live hardware & packet statistics

    def __init__(self, config: Optional[AppConfig] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.config = config or AppConfig()

        # Instantiate adapters
        self.touchpad_adapter = TouchpadInputAdapter(self.config)
        self.mouse_adapter = MouseInputAdapter(self.config)
        self.tablet_adapter = TabletInputAdapter(self.config)
        self.win_pointer_adapter = WinPointerAdapter(self.config)

        self.adapters: List[BaseInputAdapter] = [
            self.touchpad_adapter,
            self.mouse_adapter,
            self.tablet_adapter,
            self.win_pointer_adapter,
        ]

        # Active adapter
        self.active_adapter: BaseInputAdapter = self.touchpad_adapter
        self.active_device_type: InputDeviceType = InputDeviceType.TOUCHPAD

    def attach_canvas(self, canvas) -> None:
        """Attach all adapters to the target drawing canvas."""
        for adapter in self.adapters:
            adapter.attach(canvas)
        canvas.set_input_manager(self)

    def register_window_handle(self, hwnd: int) -> None:
        """Register native window handle for raw input inspection."""
        self.win_pointer_adapter.register_window(hwnd)

    def set_device_type(self, dev_type: InputDeviceType) -> None:
        """Explicitly select input device adapter or fallback."""
        if dev_type == InputDeviceType.MOUSE:
            self.active_adapter = self.mouse_adapter
            self.active_device_type = InputDeviceType.MOUSE
        elif dev_type in (InputDeviceType.PEN, InputDeviceType.TOUCHSCREEN, InputDeviceType.EXTERNAL_TABLET):
            self.active_adapter = self.tablet_adapter
            self.active_device_type = dev_type
        else:
            self.active_adapter = self.touchpad_adapter
            self.active_device_type = InputDeviceType.TOUCHPAD

        self.device_changed.emit(self.get_active_device_label())

    def set_input_mode(self, mode: InputMode) -> None:
        """Change touchpad drawing mode."""
        self.config.input_mode = mode
        self.mode_changed.emit(self.get_active_mode_label())

    def get_active_device_label(self) -> str:
        """User-friendly label for current device."""
        if self.active_adapter == self.touchpad_adapter:
            if self.config.tablet_touchpad_mode:
                return "Single-Finger Tablet (Touchpad)"
            return "Precision Touchpad"
        elif self.active_adapter == self.mouse_adapter:
            return "Mouse Fallback"
        elif self.active_adapter == self.tablet_adapter:
            return "Tablet / Pen"
        return "Unknown Device"

    def get_active_mode_label(self) -> str:
        """User-friendly label for current writing mode."""
        labels = {
            InputMode.TABLET_TOUCHPAD: "Single-Finger Tablet Mode",
            InputMode.HOLD_TO_WRITE: "Hold Space to Write",
            InputMode.DIRECT_CONTACT: "Direct Touch Inking",
            InputMode.AUTO_DWELL: "Auto-Lift Dwell",
            InputMode.CLICK_AND_DRAG: "Click / Tap to Write",
            InputMode.PEN_TABLET: "Direct Tablet Ink",
        }
        return labels.get(self.config.input_mode, "Single-Finger Tablet Mode")

    def toggle_tablet_mode(self, enabled: Optional[bool] = None) -> bool:
        """Toggle or set dedicated single-finger tablet writing mode."""
        if enabled is None:
            self.config.tablet_touchpad_mode = not self.config.tablet_touchpad_mode
        else:
            self.config.tablet_touchpad_mode = enabled

        if self.config.tablet_touchpad_mode:
            self.set_input_mode(InputMode.TABLET_TOUCHPAD)
        else:
            self.set_input_mode(InputMode.CLICK_AND_DRAG)

        self.device_changed.emit(self.get_active_device_label())
        return self.config.tablet_touchpad_mode

    def is_external_mouse_active(self) -> bool:
        """Returns True if the external mouse has actively generated raw input within the last 150ms."""
        return self.win_pointer_adapter.is_external_mouse_active()

    # -------------------------------------------------------------------------
    # Event Dispatchers (Intercepted from Window / Canvas)
    # -------------------------------------------------------------------------

    def dispatch_key_press(self, event) -> bool:
        return self.active_adapter.handle_key_press(event)

    def dispatch_key_release(self, event) -> bool:
        return self.active_adapter.handle_key_release(event)

    def dispatch_mouse_press(self, event) -> bool:
        if self.config.tablet_touchpad_mode or self.config.input_mode == InputMode.TABLET_TOUCHPAD:
            if self.is_external_mouse_active():
                return self.mouse_adapter.handle_mouse_press(event)
            return self.touchpad_adapter.handle_mouse_press(event)
        return self.active_adapter.handle_mouse_press(event)

    def dispatch_mouse_move(self, event) -> bool:
        # If in Tablet Mode: Touchpad writes like a tablet, External Mouse acts like normal mouse!
        if self.config.tablet_touchpad_mode or self.config.input_mode == InputMode.TABLET_TOUCHPAD:
            if self.is_external_mouse_active():
                # External mouse moving: Do NOT draw ink when just hovering!
                # If a previous touchpad stroke was active, commit it so mouse doesn't drag ink:
                if self.touchpad_adapter.is_writing and self.touchpad_adapter.canvas:
                    self.touchpad_adapter.canvas.end_stroke()
                    self.touchpad_adapter.is_writing = False

                # If user is explicitly holding left-click on the mouse, allow mouse drawing:
                if event.buttons() & Qt.MouseButton.LeftButton:
                    return self.mouse_adapter.handle_mouse_move(event)

                # Mouse hover/pointer navigation: DO NOT DRAW!
                return False

            # Touchpad movement: write directly like a tablet with one finger!
            return self.touchpad_adapter.handle_mouse_move(event)

        return self.active_adapter.handle_mouse_move(event)

    def dispatch_mouse_release(self, event) -> bool:
        if self.config.tablet_touchpad_mode or self.config.input_mode == InputMode.TABLET_TOUCHPAD:
            if self.is_external_mouse_active():
                return self.mouse_adapter.handle_mouse_release(event)
            return self.touchpad_adapter.handle_mouse_release(event)
        return self.active_adapter.handle_mouse_release(event)

    def dispatch_tablet_event(self, event) -> bool:
        # Tablet events take priority if stylus is detected
        if self.tablet_adapter.handle_tablet_event(event):
            if self.active_device_type != InputDeviceType.PEN:
                self.set_device_type(InputDeviceType.PEN)
            return True
        return False

    def dispatch_native_event(self, event_type, message) -> bool:
        return self.win_pointer_adapter.handle_native_event(event_type, message)
