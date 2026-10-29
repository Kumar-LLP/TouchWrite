"""
High-performance antialiased ink stroke rendering engine for TouchWrite.
"""

from typing import List, Optional
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from touchwrite.canvas.stroke import Stroke


class InkRenderer:
    """Renders vector strokes onto a QPainter device with smoothing and antialiasing."""

    @staticmethod
    def render_stroke(
        painter: QPainter,
        stroke: Stroke,
        pressure_sim: bool = True,
    ) -> None:
        """Render a single stroke with round caps and joins."""
        if not stroke.points:
            return

        color = QColor(stroke.color)
        if stroke.opacity < 1.0:
            color.setAlphaF(stroke.opacity)

        if len(stroke.points) == 1:
            # Single dot
            pt = stroke.points[0]
            r = stroke.width / 2.0
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(pt.to_qpoint(), r, r)
            return

        pen = QPen(
            color,
            stroke.width,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Draw the smooth midpoint quadratic Bézier path
        path = stroke.build_path()
        painter.drawPath(path)

    @classmethod
    def render_all(
        cls,
        painter: QPainter,
        strokes: List[Stroke],
        clip_rect: Optional[QRectF] = None,
        pressure_sim: bool = True,
    ) -> None:
        """
        Render all strokes with viewport clipping optimization.
        Strokes outside clip_rect are quickly skipped.
        """
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        for stroke in strokes:
            if clip_rect is not None:
                # Viewport culling
                if not stroke.get_bounding_rect().intersects(clip_rect):
                    continue
            cls.render_stroke(painter, stroke, pressure_sim)

        painter.restore()
