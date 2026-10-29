"""
Base input adapter and event abstractions for TouchWrite.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Optional, TYPE_CHECKING
from PySide6.QtCore import QPointF

if TYPE_CHECKING:
    from touchwrite.canvas.canvas import TouchCanvas


class InputEventType(str, Enum):
    """Types of input actions translated to drawing."""
    DOWN = "down"        # Pen placed on surface
    MOVE = "move"        # Continuous stroke movement
    UP = "up"            # Pen lifted from surface
    CANCEL = "cancel"    # Stroke cancelled


class InputDeviceType(str, Enum):
    """Detected physical or virtual input device."""
    TOUCHPAD = "Precision Touchpad"
    MOUSE = "Standard Mouse"
    PEN = "Stylus / Active Pen"
    TOUCHSCREEN = "Touchscreen"
    EXTERNAL_TABLET = "External Graphics Tablet"
    UNKNOWN = "Unknown Device"


@dataclass
class InputEvent:
    """Normalized input event ready for canvas consumption."""
    event_type: InputEventType
    screen_pos: QPointF
    canvas_pos: QPointF
    pressure: float = 1.0
    device_type: InputDeviceType = InputDeviceType.TOUCHPAD
    timestamp: float = field(default_factory=time.time)


class BaseInputAdapter(ABC):
    """Abstract base class for all input hardware and gesture adapters."""

    def __init__(self, name: str, device_type: InputDeviceType):
        self.name = name
        self.device_type = device_type
        self.is_enabled: bool = True
        self.canvas: Optional["TouchCanvas"] = None

    def attach(self, canvas: "TouchCanvas") -> None:
        """Attach adapter to a target canvas."""
        self.canvas = canvas

    def detach(self) -> None:
        """Detach adapter from canvas."""
        self.canvas = None

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this hardware/API is currently usable."""
        raise NotImplementedError

    def handle_mouse_press(self, event) -> bool:
        """Return True if event was handled by this adapter."""
        return False

    def handle_mouse_move(self, event) -> bool:
        return False

    def handle_mouse_release(self, event) -> bool:
        return False

    def handle_key_press(self, event) -> bool:
        return False

    def handle_key_release(self, event) -> bool:
        return False

    def handle_tablet_event(self, event) -> bool:
        return False

    def handle_touch_event(self, event) -> bool:
        return False

    def handle_native_event(self, event_type, message) -> bool:
        return False
