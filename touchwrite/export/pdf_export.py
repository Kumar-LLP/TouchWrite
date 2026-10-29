"""
High-resolution vector PDF exporter for TouchWrite notebooks.
"""

from typing import List
from PySide6.QtCore import QRectF, QMarginsF
from PySide6.QtGui import QPdfWriter, QPainter, QPageSize, QPageLayout
from touchwrite.canvas.stroke import Stroke
from touchwrite.canvas.renderer import InkRenderer
from touchwrite.canvas.paper import PaperRenderer
from touchwrite.config import AppConfig


def export_to_pdf(
    filepath: str,
    strokes: List[Stroke],
    config: AppConfig,
    include_background: bool = True,
) -> bool:
    """
    Export handwritten strokes to a crisp vector PDF document using QPdfWriter.
    """
    writer = QPdfWriter(filepath)
    writer.setResolution(300)  # 300 DPI print quality

    # Standard A4 portrait layout with 0 margins (full bleed virtual paper)
    page_layout = QPageLayout(
        QPageSize(QPageSize.PageSizeId.A4),
        QPageLayout.Orientation.Portrait,
        QMarginsF(0, 0, 0, 0),
    )
    writer.setPageLayout(page_layout)

    painter = QPainter(writer)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    # Calculate scale factor to map virtual canvas to PDF page pixel dimensions
    page_rect = page_layout.paintRectPixels(300)
    scale_x = page_rect.width() / float(config.canvas_width)
    scale_y = page_rect.height() / float(config.canvas_height)
    scale = min(scale_x, scale_y)

    painter.scale(scale, scale)

    # Render paper background
    paper_rect = QRectF(0, 0, config.canvas_width, config.canvas_height)
    if include_background:
        PaperRenderer.render(
            painter=painter,
            rect=paper_rect,
            style=config.paper_style,
            spacing=config.paper_line_spacing,
            margin_x=config.paper_margin,
            dark_mode=False,
        )

    # Render ink strokes
    InkRenderer.render_all(
        painter=painter,
        strokes=strokes,
        clip_rect=None,
        pressure_sim=config.pressure_simulation,
    )

    painter.end()
    return True
