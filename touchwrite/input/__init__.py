"""
Input subsystem for TouchWrite application.
"""

from touchwrite.input.base import BaseInputAdapter, InputDeviceType, InputEvent, InputEventType
from touchwrite.input.touchpad_adapter import TouchpadInputAdapter
from touchwrite.input.mouse_adapter import MouseInputAdapter
from touchwrite.input.tablet_adapter import TabletInputAdapter
from touchwrite.input.win_pointer_adapter import WinPointerAdapter
from touchwrite.input.manager import InputManager

__all__ = [
    "BaseInputAdapter",
    "InputDeviceType",
    "InputEvent",
    "InputEventType",
    "TouchpadInputAdapter",
    "MouseInputAdapter",
    "TabletInputAdapter",
    "WinPointerAdapter",
    "InputManager",
]
