"""
Unit tests for input adapters and input manager.
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QKeyEvent
from touchwrite.config import AppConfig, InputMode
from touchwrite.canvas.canvas import TouchCanvas
from touchwrite.input.manager import InputManager
from touchwrite.input.base import InputDeviceType

_app = QApplication.instance() or QApplication([])


def test_input_manager_initialization():
    config = AppConfig()
    canvas = TouchCanvas(config)
    mgr = InputManager(config)
    mgr.attach_canvas(canvas)

    assert mgr.active_device_type == InputDeviceType.TOUCHPAD
    assert "Touchpad" in mgr.get_active_device_label()


def test_input_manager_device_switching():
    mgr = InputManager()
    mgr.set_device_type(InputDeviceType.MOUSE)
    assert mgr.active_device_type == InputDeviceType.MOUSE
    assert "Mouse" in mgr.get_active_device_label()

    mgr.set_device_type(InputDeviceType.PEN)
    assert mgr.active_device_type == InputDeviceType.PEN
    assert "Tablet" in mgr.get_active_device_label()


def test_hold_to_write_keyboard_trigger():
    config = AppConfig(input_mode=InputMode.HOLD_TO_WRITE)
    canvas = TouchCanvas(config)
    mgr = InputManager(config)
    mgr.attach_canvas(canvas)

    # Simulate Space key press
    press_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier)
    handled = mgr.dispatch_key_press(press_event)
    assert handled is True
    assert mgr.touchpad_adapter.is_trigger_held is True

    # Simulate Space key release
    release_event = QKeyEvent(QKeyEvent.Type.KeyRelease, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier)
    handled_rel = mgr.dispatch_key_release(release_event)
    assert handled_rel is True
    assert mgr.touchpad_adapter.is_trigger_held is False


def test_two_finger_tablet_mode():
    config = AppConfig(input_mode=InputMode.TABLET_TOUCHPAD, tablet_touchpad_mode=True, finger_lift_timeout_ms=50)
    canvas = TouchCanvas(config)
    mgr = InputManager(config)
    mgr.attach_canvas(canvas)

    assert mgr.config.tablet_touchpad_mode is True
    assert "Tablet" in mgr.get_active_device_label()

    # Mark hardware source as Touchpad with 2 fingers contacting!
    import time
    mgr.win_pointer_adapter.last_source = "TOUCHPAD"
    mgr.win_pointer_adapter.last_touchpad_time = time.time()
    mgr.win_pointer_adapter.contact_count = 2

    # Move 2 fingers inside paper -> should start and continue stroke!
    from PySide6.QtGui import QMouseEvent
    pt1 = QPointF(200, 200)
    move1 = QMouseEvent(QMouseEvent.Type.MouseMove, pt1, pt1, Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
    handled1 = mgr.dispatch_mouse_move(move1)
    assert handled1 is True
    assert canvas.is_inking is True
    assert len(canvas.current_stroke.points) >= 1

    pt2 = QPointF(210, 220)
    move2 = QMouseEvent(QMouseEvent.Type.MouseMove, pt2, pt2, Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
    handled2 = mgr.dispatch_mouse_move(move2)
    assert handled2 is True
    assert len(canvas.current_stroke.points) >= 2

    # Simulate finger lift timeout -> stroke finishes!
    mgr.touchpad_adapter._on_dwell_timeout()
    assert canvas.is_inking is False
    assert len(canvas.strokes) == 1


def test_one_finger_normal_mouse_mode():
    config = AppConfig(input_mode=InputMode.TABLET_TOUCHPAD, tablet_touchpad_mode=True)
    canvas = TouchCanvas(config)
    mgr = InputManager(config)
    mgr.attach_canvas(canvas)

    import time
    from PySide6.QtGui import QMouseEvent

    # 1 finger on touchpad
    mgr.win_pointer_adapter.last_source = "TOUCHPAD"
    mgr.win_pointer_adapter.last_touchpad_time = time.time()
    mgr.win_pointer_adapter.contact_count = 1

    # Moving 1 finger hovering MUST NOT ink (acts as normal mouse pointer)
    pt = QPointF(250, 250)
    move_one = QMouseEvent(QMouseEvent.Type.MouseMove, pt, pt, Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
    handled = mgr.dispatch_mouse_move(move_one)
    assert handled is False
    assert canvas.is_inking is False
    assert len(canvas.strokes) == 0


def test_three_finger_page_scrolling():
    config = AppConfig(input_mode=InputMode.TABLET_TOUCHPAD, tablet_touchpad_mode=True)
    canvas = TouchCanvas(config)
    mgr = InputManager(config)
    mgr.attach_canvas(canvas)

    import time
    from PySide6.QtGui import QMouseEvent

    # 3 fingers on touchpad
    mgr.win_pointer_adapter.last_source = "TOUCHPAD"
    mgr.win_pointer_adapter.last_touchpad_time = time.time()
    mgr.win_pointer_adapter.contact_count = 3

    init_pan = QPointF(canvas.pan_offset.x(), canvas.pan_offset.y())

    # Moving 3 fingers pans/scrolls the canvas
    pt1 = QPointF(200, 200)
    move1 = QMouseEvent(QMouseEvent.Type.MouseMove, pt1, pt1, Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
    mgr.dispatch_mouse_move(move1)

    pt2 = QPointF(210, 230)
    move2 = QMouseEvent(QMouseEvent.Type.MouseMove, pt2, pt2, Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
    mgr.dispatch_mouse_move(move2)

    assert canvas.is_inking is False
    assert canvas.pan_offset != init_pan


def test_external_mouse_does_not_draw_by_hovering_in_tablet_mode():
    config = AppConfig(input_mode=InputMode.TABLET_TOUCHPAD, tablet_touchpad_mode=True)
    canvas = TouchCanvas(config)
    mgr = InputManager(config)
    mgr.attach_canvas(canvas)

    import time
    from PySide6.QtGui import QMouseEvent

    # Mark hardware source as external Mouse
    mgr.win_pointer_adapter.last_source = "MOUSE"
    mgr.win_pointer_adapter.last_mouse_time = time.time()
    mgr.win_pointer_adapter.last_touchpad_time = 0.0

    # Moving external mouse without clicking MUST NOT ink!
    pt = QPointF(300, 300)
    move_hover = QMouseEvent(QMouseEvent.Type.MouseMove, pt, pt, Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
    handled = mgr.dispatch_mouse_move(move_hover)
    assert handled is False
    assert canvas.is_inking is False
    assert len(canvas.strokes) == 0

    # But left-click dragging with the mouse allows standard mouse drawing
    move_drag = QMouseEvent(QMouseEvent.Type.MouseMove, pt, pt, Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    mgr.dispatch_mouse_press(move_drag)
    assert canvas.is_inking is True
    mgr.dispatch_mouse_release(move_drag)
    assert canvas.is_inking is False
    assert len(canvas.strokes) == 1


def test_toggle_tablet_mode():
    mgr = InputManager()
    assert mgr.config.tablet_touchpad_mode is True

    # Toggle OFF
    state = mgr.toggle_tablet_mode()
    assert state is False
    assert mgr.config.tablet_touchpad_mode is False

    # Toggle ON
    state = mgr.toggle_tablet_mode()
    assert state is True
    assert mgr.config.tablet_touchpad_mode is True


def test_tablet_mode_jump_detection_separates_strokes():
    config = AppConfig(input_mode=InputMode.TABLET_TOUCHPAD, tablet_touchpad_mode=True, finger_lift_timeout_ms=50)
    canvas = TouchCanvas(config)
    mgr = InputManager(config)
    mgr.attach_canvas(canvas)

    import time
    from PySide6.QtGui import QMouseEvent

    mgr.win_pointer_adapter.last_source = "TOUCHPAD"
    mgr.win_pointer_adapter.last_touchpad_time = time.time()
    mgr.win_pointer_adapter.contact_count = 2

    # Stroke 1: Draw letter "C" with 2 fingers
    pt1 = QPointF(200, 200)
    move1 = QMouseEvent(QMouseEvent.Type.MouseMove, pt1, pt1, Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
    mgr.dispatch_mouse_move(move1)

    pt2 = QPointF(205, 210)
    move2 = QMouseEvent(QMouseEvent.Type.MouseMove, pt2, pt2, Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
    mgr.dispatch_mouse_move(move2)
    assert len(canvas.strokes) == 0
    assert canvas.is_inking is True

    # Fingers lift and touch down to start "h" 80 pixels away
    # Jump detection must commit stroke 1 and start stroke 2 without an unwanted connecting line!
    pt3 = QPointF(290, 200)
    move3 = QMouseEvent(QMouseEvent.Type.MouseMove, pt3, pt3, Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
    mgr.dispatch_mouse_move(move3)
    assert len(canvas.strokes) == 1  # Stroke 1 committed!
    assert canvas.is_inking is True  # Stroke 2 in progress!

    # Finish stroke 2
    mgr.touchpad_adapter._on_dwell_timeout()
    assert len(canvas.strokes) == 2
    assert canvas.is_inking is False


def test_two_finger_wheel_event_inks_and_three_finger_scrolls():
    from PySide6.QtGui import QWheelEvent
    from PySide6.QtCore import QPoint

    config = AppConfig(input_mode=InputMode.TABLET_TOUCHPAD, tablet_touchpad_mode=True)
    canvas = TouchCanvas(config)
    mgr = InputManager(config)
    mgr.attach_canvas(canvas)

    # 1. Two-finger gesture event (source == SynthesizedBySystem, non-zero pixelDelta) -> INKS!
    mgr.win_pointer_adapter.contact_count = 2
    pt = QPointF(200, 200)
    wheel_2f = QWheelEvent(
        pt, pt, QPoint(0, 5), QPoint(0, 60),
        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.ScrollUpdate, False, Qt.MouseEventSource.MouseEventSynthesizedBySystem
    )
    canvas.wheelEvent(wheel_2f)
    assert canvas.is_inking is True

    # 2. Three-finger gesture event (contact_count == 3) -> SCROLLS/PANS THE PAGE!
    mgr.win_pointer_adapter.contact_count = 3
    init_pan = QPointF(canvas.pan_offset.x(), canvas.pan_offset.y())
    wheel_3f = QWheelEvent(
        pt, pt, QPoint(10, 20), QPoint(0, 120),
        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.ScrollUpdate, False, Qt.MouseEventSource.MouseEventSynthesizedBySystem
    )
    canvas.wheelEvent(wheel_3f)
    assert canvas.pan_offset != init_pan


def test_device_discrimination_telemetry():
    from touchwrite.input.win_pointer_adapter import WinPointerAdapter
    adapter = WinPointerAdapter()

    assert adapter.last_source == "TOUCHPAD"
    assert adapter.is_touchpad_active() is True
    assert adapter.is_external_mouse_active() is False

    # Simulate external mouse event
    import time
    adapter.last_source = "MOUSE"
    adapter.last_mouse_time = time.time()
    assert adapter.is_external_mouse_active() is True
    assert adapter.is_touchpad_active() is False

    # Simulate mouse inactive after 200ms
    adapter.last_mouse_time = time.time() - 0.2
    assert adapter.is_external_mouse_active() is False
    assert adapter.is_touchpad_active() is True

