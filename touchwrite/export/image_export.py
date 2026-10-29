"""
PNG raster image exporter with high-DPI scaling and background transparency options.
"""

from typing import List, Optional
from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QImage, QPainter, QColor
from touchwrite.canvas.stroke import Stroke
from touchwrite.canvas.renderer import InkRenderer
from touchwrite.canvas.paper import PaperRenderer
from touchwrite.config import AppConfig, PaperStyle


def export_to_png(
    filepath: str,
    strokes: List[Stroke],
    config: AppConfig,
    include_background: bool = True,
    transparent_bg: bool = False,
    scale: float = 1.0,
    crop_to_content: bool = False,
) -> bool:
    """
    Export canvas handwriting strokes to a high-resolution PNG image.
    """
    page_w = int(config.canvas_width * scale)
    page_h = int(config.canvas_height * scale)

    if crop_to_content and strokes:
        # Compute combined bounding box of all strokes
        combined = strokes[0].get_bounding_rect()
        for s in strokes[1:]:
            combined = combined.united(s.get_bounding_rect())
        # Add margin
        margin = 40.0
        render_rect = combined.adjusted(-margin, -margin, margin, margin)
        # Ensure positive
        x = max(0.0, render_rect.left())
        y = max(0.0, render_rect.top())
        w = max(100.0, render_rect.width())
        h = max(100.0, render_rect.height())
        target_size = QSize(int(w * scale), int(h * scale))
        offset_x = -x
        offset_y = -y
        base_rect = QRectF(0, 0, w, h)
    else:
        target_size = QSize(page_w, page_h)
        offset_x = 0.0
        offset_y = 0.0
        base_rect = QRectF(0, 0, config.canvas_width, config.canvas_height)

    image = QImage(target_size, QImage.Format.Format_ARGB32_Premultiplied)

    if transparent_bg:
        image.fill(Qt.GlobalColor.transparent)
    else:
        image.fill(PaperRenderer.LIGHT_BG)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.scale(scale, scale)
    painter.translate(offset_x, offset_y)

    # Draw paper background if requested and not transparent
    if include_background and not transparent_bg:
        paper_full_rect = QRectF(0, 0, config.canvas_width, config.canvas_height)
        PaperRenderer.render(
            painter=painter,
            rect=paper_full_rect,
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
    return image.save(filepath, "PNG")
