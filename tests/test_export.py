"""
Unit tests for PNG, SVG, and PDF exporters.
"""

import os
from PySide6.QtWidgets import QApplication
from touchwrite.config import AppConfig, PaperStyle
from touchwrite.canvas.stroke import Stroke, StrokePoint
from touchwrite.export.image_export import export_to_png
from touchwrite.export.svg_export import export_to_svg
from touchwrite.export.pdf_export import export_to_pdf

_app = QApplication.instance() or QApplication([])


def create_sample_strokes():
    s1 = Stroke(color="#111827", width=3.0)
    s1.add_point(StrokePoint(100, 100))
    s1.add_point(StrokePoint(200, 150))
    s1.add_point(StrokePoint(300, 120))

    s2 = Stroke(color="#991B1B", width=4.0)
    s2.add_point(StrokePoint(150, 250))
    s2.add_point(StrokePoint(250, 250))
    return [s1, s2]


def test_png_export(tmp_path):
    config = AppConfig()
    strokes = create_sample_strokes()
    filepath = str(tmp_path / "out.png")

    success = export_to_png(filepath, strokes, config, include_background=True)
    assert success is True
    assert os.path.exists(filepath)
    assert os.path.getsize(filepath) > 1000


def test_svg_export(tmp_path):
    config = AppConfig(paper_style=PaperStyle.RULED)
    strokes = create_sample_strokes()
    filepath = str(tmp_path / "out.svg")

    success = export_to_svg(filepath, strokes, config, include_background=True)
    assert success is True
    assert os.path.exists(filepath)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "<svg" in content
    assert "class=\"ink-stroke\"" in content
    assert "</svg>" in content


def test_pdf_export(tmp_path):
    config = AppConfig()
    strokes = create_sample_strokes()
    filepath = str(tmp_path / "out.pdf")

    success = export_to_pdf(filepath, strokes, config, include_background=True)
    assert success is True
    assert os.path.exists(filepath)

    with open(filepath, "rb") as f:
        header = f.read(5)
    assert header == b"%PDF-"
