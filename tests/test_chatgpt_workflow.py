"""
End-to-end integration test verifying the core objective:
Drawing letters 'C', 'h', 'a', 't', 'G', 'P', 'T' with finger writing,
preserving strokes as vector ink, erasing, undoing, redoing, and exporting.
"""

import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from touchwrite.config import AppConfig, ToolMode, PaperStyle, InputMode
from touchwrite.ui.main_window import MainWindow
from touchwrite.canvas.stroke import Stroke, StrokePoint

_app = QApplication.instance() or QApplication([])


def test_draw_chatgpt_letters_and_full_workflow(tmp_path):
    config = AppConfig()
    win = MainWindow(config)
    canvas = win.canvas

    # 1. Simulate finger-drawing letters: C, h, a, t, G, P, T
    # Letter 'C' (arc from right, curving left, down, and back right)
    canvas.start_stroke(QPointF(100, 100))
    canvas.continue_stroke(QPointF(80, 120))
    canvas.continue_stroke(QPointF(80, 160))
    canvas.continue_stroke(QPointF(100, 180))
    canvas.end_stroke()

    # Letter 'h' (stem down, then arch)
    canvas.start_stroke(QPointF(130, 80))
    canvas.continue_stroke(QPointF(130, 180))
    canvas.end_stroke()
    canvas.start_stroke(QPointF(130, 130))
    canvas.continue_stroke(QPointF(150, 120))
    canvas.continue_stroke(QPointF(160, 150))
    canvas.continue_stroke(QPointF(160, 180))
    canvas.end_stroke()

    # Letter 'a'
    canvas.start_stroke(QPointF(190, 140))
    canvas.continue_stroke(QPointF(175, 160))
    canvas.continue_stroke(QPointF(190, 180))
    canvas.continue_stroke(QPointF(205, 160))
    canvas.continue_stroke(QPointF(205, 140))
    canvas.continue_stroke(QPointF(205, 180))
    canvas.end_stroke()

    # Letter 't'
    canvas.start_stroke(QPointF(230, 100))
    canvas.continue_stroke(QPointF(230, 180))
    canvas.end_stroke()
    canvas.start_stroke(QPointF(215, 125))
    canvas.continue_stroke(QPointF(245, 125))
    canvas.end_stroke()

    # Letter 'G'
    canvas.start_stroke(QPointF(290, 100))
    canvas.continue_stroke(QPointF(265, 140))
    canvas.continue_stroke(QPointF(290, 180))
    canvas.continue_stroke(QPointF(305, 180))
    canvas.continue_stroke(QPointF(305, 145))
    canvas.continue_stroke(QPointF(285, 145))
    canvas.end_stroke()

    # Letter 'P'
    canvas.start_stroke(QPointF(330, 100))
    canvas.continue_stroke(QPointF(330, 180))
    canvas.end_stroke()
    canvas.start_stroke(QPointF(330, 100))
    canvas.continue_stroke(QPointF(360, 115))
    canvas.continue_stroke(QPointF(330, 135))
    canvas.end_stroke()

    # Letter 'T'
    canvas.start_stroke(QPointF(380, 100))
    canvas.continue_stroke(QPointF(420, 100))
    canvas.end_stroke()
    canvas.start_stroke(QPointF(400, 100))
    canvas.continue_stroke(QPointF(400, 180))
    canvas.end_stroke()

    # 2. Verify all strokes exist as authentic vector ink
    total_strokes = len(canvas.strokes)
    assert total_strokes == 11  # Multi-stroke letters ('h', 't', 'P', 'T')
    assert win.status_widget.stroke_label.text() == f"Strokes: {total_strokes}"

    # Verify that strokes are NOT converted into fonts/text:
    for stroke in canvas.strokes:
        assert isinstance(stroke, Stroke)
        assert len(stroke.points) >= 2
        path = stroke.build_path()
        assert not path.isEmpty()

    # 3. Test Undo and Redo
    win.canvas.undo()
    assert len(canvas.strokes) == total_strokes - 1

    win.canvas.redo()
    assert len(canvas.strokes) == total_strokes

    # 4. Test Stroke Eraser
    canvas.set_tool(ToolMode.ERASER)
    # Erase the 'C' stroke at (100, 100)
    canvas.start_stroke(QPointF(100, 100))
    canvas.end_stroke()
    assert len(canvas.strokes) == total_strokes - 1

    # Undo erase restores 'C'
    canvas.undo()
    assert len(canvas.strokes) == total_strokes

    # 5. Test Save & Load Session
    save_path = str(tmp_path / "chatgpt_session.touchwrite")
    win.session_manager.save_session(save_path, canvas.strokes)
    assert os.path.exists(save_path)

    # Reset canvas
    win._on_action_new()
    assert len(canvas.strokes) == 0

    # Load session back
    win._load_from_filepath(save_path)
    assert len(canvas.strokes) == total_strokes

    # 6. Test Toolbar Settings and Preferences
    assert win.toolbar.btn_settings is not None
    assert win.toolbar.btn_pen.isChecked() is True

    # 7. Test Export to PNG, SVG, PDF
    png_path = str(tmp_path / "chatgpt.png")
    svg_path = str(tmp_path / "chatgpt.svg")
    pdf_path = str(tmp_path / "chatgpt.pdf")

    from touchwrite.export.image_export import export_to_png
    from touchwrite.export.svg_export import export_to_svg
    from touchwrite.export.pdf_export import export_to_pdf

    assert export_to_png(png_path, canvas.strokes, config) is True
    assert export_to_svg(svg_path, canvas.strokes, config) is True
    assert export_to_pdf(pdf_path, canvas.strokes, config) is True

    assert os.path.getsize(png_path) > 5000
    assert os.path.getsize(svg_path) > 1000
    assert os.path.getsize(pdf_path) > 1000

    win.close()
