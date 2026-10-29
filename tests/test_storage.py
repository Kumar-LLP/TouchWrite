"""
Unit tests for session serialization, validation, and disk operations.
"""

import os
import tempfile
import pytest
from touchwrite.config import AppConfig, PaperStyle
from touchwrite.canvas.stroke import Stroke, StrokePoint
from touchwrite.storage.json_format import (
    serialize_session,
    deserialize_session,
    save_session_file,
    load_session_file,
)
from touchwrite.storage.session_manager import SessionManager


def test_serialize_and_deserialize():
    config = AppConfig(paper_style=PaperStyle.GRID)
    stroke = Stroke(color="#065F46", width=2.5)
    stroke.add_point(StrokePoint(12.3, 45.6, pressure=0.9))

    data = serialize_session([stroke], config)
    assert data["app"] == "TouchWrite"
    assert data["version"] == "1.0"
    assert data["canvas"]["paper_style"] == "grid"
    assert len(data["strokes"]) == 1

    restored_strokes, meta = deserialize_session(data)
    assert len(restored_strokes) == 1
    assert restored_strokes[0].color == "#065F46"
    assert meta["paper_style"] == "grid"


def test_file_save_and_load(tmp_path):
    config = AppConfig()
    stroke = Stroke(color="#111827", width=3.0)
    stroke.add_point(StrokePoint(10, 20))
    stroke.add_point(StrokePoint(30, 40))

    file_path = str(tmp_path / "test_notes.touchwrite")
    save_session_file(file_path, [stroke], config)
    assert os.path.exists(file_path)

    loaded_strokes, meta = load_session_file(file_path)
    assert len(loaded_strokes) == 1
    assert len(loaded_strokes[0].points) == 2


def test_corrupt_file_handling():
    with pytest.raises(ValueError):
        deserialize_session({"app": "WrongApp", "version": "1.0"})

    with pytest.raises(ValueError):
        deserialize_session("Not A Dict")


def test_session_manager():
    sm = SessionManager()
    assert sm.is_dirty is False
    sm.set_dirty(True)
    assert sm.is_dirty is True
    assert "*" in sm.get_document_name() or "Untitled" in sm.get_document_name()
