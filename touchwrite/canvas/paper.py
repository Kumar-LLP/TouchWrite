"""
Paper background rendering for notebook-like appearance in TouchWrite.
"""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from touchwrite.config import PaperStyle


class PaperRenderer:
    """Renders blank, ruled, or grid paper notebook backgrounds."""

    # Color palettes for light and dark paper
    LIGHT_BG = QColor("#FAFAF9")       # Warm paper white
    LIGHT_LINE = QColor("#D4D4D8")     # Subtle slate line
    LIGHT_MARGIN = QColor("#FCA5A5")   # Notebook red margin line

    DARK_BG = QColor("#18181B")        # Zinc dark paper
    DARK_LINE = QColor("#27272A")      # Dark subtle line
    DARK_MARGIN = QColor("#7F1D1D")    # Dark red margin line

    @classmethod
    def render(
        cls,
        painter: QPainter,
        rect: QRectF,
        style: PaperStyle = PaperStyle.RULED,
        spacing: int = 34,
        margin_x: int = 70,
        dark_mode: bool = False,
    ) -> None:
        """
        Render the paper background onto the specified canvas rectangle.
        Only draws within the clipping bounds for high performance.
        """
        bg_col = cls.DARK_BG if dark_mode else cls.LIGHT_BG
        line_col = cls.DARK_LINE if dark_mode else cls.LIGHT_LINE
        margin_col = cls.DARK_MARGIN if dark_mode else cls.LIGHT_MARGIN

        # Fill background sheet
        painter.fillRect(rect, QBrush(bg_col))

        if style == PaperStyle.BLANK:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # Draw Ruled Lines
        if style == PaperStyle.RULED:
            pen = QPen(line_col, 1.0)
            painter.setPen(pen)

            start_y = int(rect.top() // spacing * spacing)
            end_y = int(rect.bottom() + spacing)

            for y in range(start_y, end_y, spacing):
                if y >= rect.top() and y <= rect.bottom():
                    painter.drawLine(int(rect.left()), y, int(rect.right()), y)

            # Draw vertical notebook margin line
            if margin_x > 0 and margin_x <= rect.right():
                margin_pen = QPen(margin_col, 1.5)
                painter.setPen(margin_pen)
                painter.drawLine(margin_x, int(rect.top()), margin_x, int(rect.bottom()))

        # Draw Grid / Graph Lines
        elif style == PaperStyle.GRID:
            pen = QPen(line_col, 0.8)
            painter.setPen(pen)

            grid_size = max(16, spacing)
            start_x = int(rect.left() // grid_size * grid_size)
            end_x = int(rect.right() + grid_size)
            start_y = int(rect.top() // grid_size * grid_size)
            end_y = int(rect.bottom() + grid_size)

            # Horizontal grid lines
            for y in range(start_y, end_y, grid_size):
                if y >= rect.top() and y <= rect.bottom():
                    painter.drawLine(int(rect.left()), y, int(rect.right()), y)

            # Vertical grid lines
            for x in range(start_x, end_x, grid_size):
                if x >= rect.left() and x <= rect.right():
                    painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))

        painter.restore()
