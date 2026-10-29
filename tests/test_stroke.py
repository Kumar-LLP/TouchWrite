"""
Unit tests for stroke models and Bézier smoothing.
"""

import pytest
from PySide6.QtCore import QPointF
from touchwrite.canvas.stroke import Stroke, StrokePoint


def test_stroke_point_serialization():
    pt = StrokePoint(100.5, 200.75, pressure=0.85, timestamp=1000.0)
    data = pt.to_dict()
    assert data["x"] == 100.5
    assert data["y"] == 200.75
    assert data["p"] == 0.85
    assert data["t"] == 1000.0

    restored = StrokePoint.from_dict(data)
    assert restored.x == pt.x
    assert restored.y == pt.y
    assert restored.pressure == pt.pressure


def test_stroke_creation_and_path():
    stroke = Stroke(color="#1E40AF", width=4.0)
    assert len(stroke.points) == 0

    # Add points
    stroke.add_point(StrokePoint(10.0, 10.0))
    stroke.add_point(StrokePoint(50.0, 50.0))
    stroke.add_point(StrokePoint(100.0, 80.0))
    assert len(stroke.points) == 3

    # Verify smooth path generation
    path = stroke.build_path()
    assert not path.isEmpty()
    assert stroke.get_bounding_rect().width() > 0


def test_stroke_deduplication():
    stroke = Stroke()
    stroke.add_point(StrokePoint(50.0, 50.0))
    # Co-located point (less than 0.5px away) should be skipped
    stroke.add_point(StrokePoint(50.1, 50.1))
    assert len(stroke.points) == 1

    # Distant point should be added
    stroke.add_point(StrokePoint(55.0, 55.0))
    assert len(stroke.points) == 2


def test_stroke_distance_for_eraser():
    stroke = Stroke(width=3.0)
    stroke.add_point(StrokePoint(10.0, 10.0))
    stroke.add_point(StrokePoint(100.0, 10.0))

    # Point right on the line
    dist_on_line = stroke.distance_to_point(QPointF(50.0, 10.0))
    assert dist_on_line < 0.1

    # Point 15 units perpendicular away
    dist_away = stroke.distance_to_point(QPointF(50.0, 25.0))
    assert pytest.approx(dist_away, 0.1) == 15.0


def test_stroke_serialization():
    stroke = Stroke(color="#991B1B", width=5.0)
    stroke.add_point(StrokePoint(0.0, 0.0))
    stroke.add_point(StrokePoint(10.0, 20.0))

    data = stroke.to_dict()
    assert data["color"] == "#991B1B"
    assert data["width"] == 5.0
    assert len(data["points"]) == 2

    restored = Stroke.from_dict(data)
    assert restored.color == "#991B1B"
    assert restored.width == 5.0
    assert len(restored.points) == 2
