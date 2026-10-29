"""
Unit tests for TouchCanvas drawing surface, zooming, and undo/redo history.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from touchwrite.config import AppConfig, ToolMode
from touchwrite.canvas.canvas import TouchCanvas

# Ensure QApplication exists for widget testing
_app = QApplication.instance() or QApplication([])


def test_canvas_initialization():
    config = AppConfig()
    canvas = TouchCanvas(config)
    assert len(canvas.strokes) == 0
    assert canvas.zoom == 1.0
    assert canvas.active_tool == ToolMode.PEN


def test_coordinate_transforms():
    canvas = TouchCanvas()
    canvas.pan_offset = QPointF(50.0, 50.0)
    canvas.zoom = 2.0

    # Screen point (150, 150) -> canvas point ((150 - 50)/2 = 50, (150 - 50)/2 = 50)
    c_pt = canvas.screen_to_canvas(QPointF(150.0, 150.0))
    assert pytest.approx(c_pt.x()) == 50.0
    assert pytest.approx(c_pt.y()) == 50.0

    # Reverse
    s_pt = canvas.canvas_to_screen(c_pt)
    assert pytest.approx(s_pt.x()) == 150.0
    assert pytest.approx(s_pt.y()) == 150.0


def test_stroke_lifecycle():
    canvas = TouchCanvas()
    assert len(canvas.strokes) == 0

    canvas.start_stroke(QPointF(10.0, 10.0))
    assert canvas.is_inking is True
    assert canvas.current_stroke is not None

    canvas.continue_stroke(QPointF(20.0, 20.0))
    canvas.continue_stroke(QPointF(30.0, 30.0))
    assert len(canvas.current_stroke.points) == 3

    canvas.end_stroke()
    assert canvas.is_inking is False
    assert len(canvas.strokes) == 1
    assert len(canvas.strokes[0].points) == 3


def test_undo_and_redo():
    canvas = TouchCanvas()
    canvas.start_stroke(QPointF(0, 0))
    canvas.continue_stroke(QPointF(10, 10))
    canvas.end_stroke()

    assert len(canvas.strokes) == 1
    assert canvas.history.can_undo is True

    # Undo
    canvas.undo()
    assert len(canvas.strokes) == 0
    assert canvas.history.can_redo is True

    # Redo
    canvas.redo()
    assert len(canvas.strokes) == 1


def test_stroke_eraser():
    canvas = TouchCanvas()
    # Stroke 1: horizontal line from (0, 10) to (100, 10)
    canvas.start_stroke(QPointF(0, 10))
    canvas.continue_stroke(QPointF(100, 10))
    canvas.end_stroke()

    # Stroke 2: vertical line from (500, 0) to (500, 100)
    canvas.start_stroke(QPointF(500, 0))
    canvas.continue_stroke(QPointF(500, 100))
    canvas.end_stroke()

    assert len(canvas.strokes) == 2

    # Switch to eraser and erase near Stroke 1
    canvas.set_tool(ToolMode.ERASER)
    canvas.start_stroke(QPointF(50, 12))  # Very close to Stroke 1
    canvas.end_stroke()

    # Stroke 1 should be gone, Stroke 2 should remain
    assert len(canvas.strokes) == 1
    assert canvas.strokes[0].points[0].x == 500

    # Undo should restore Stroke 1
    canvas.undo()
    assert len(canvas.strokes) == 2


def test_clear_canvas():
    canvas = TouchCanvas()
    canvas.start_stroke(QPointF(0, 0))
    canvas.end_stroke()
    assert len(canvas.strokes) == 1

    canvas.clear_canvas()
    assert len(canvas.strokes) == 0

    # Undo clear
    canvas.undo()
    assert len(canvas.strokes) == 1
