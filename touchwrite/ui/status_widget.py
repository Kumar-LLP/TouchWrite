"""
Status bar widgets indicating input device, active inking state, zoom, and coordinates.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt


class StatusBarWidget(QWidget):
    """
    Modular status widget providing real-time telemetry:
    - Input device indicator (Touchpad / Mouse / Pen)
    - Active inking indicator (Glowing green when writing)
    - Virtual canvas coordinates
    - Zoom level indicator
    - Total stroke count
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 1. Input Device Badge
        self.device_badge = QLabel("📱 Single-Finger Tablet Mode")
        self.device_badge.setStyleSheet(
            "font-weight: 700; padding: 2px 8px; border-radius: 4px; background: rgba(37, 99, 235, 0.15); color: #2563EB;"
        )
        layout.addWidget(self.device_badge)

        # 2. Inking Activity Glow Indicator
        self.inking_badge = QLabel("○ Idle")
        self.inking_badge.setStyleSheet(
            "font-weight: 500; padding: 2px 8px; border-radius: 4px; background: rgba(156, 163, 175, 0.15); color: #6B7280;"
        )
        layout.addWidget(self.inking_badge)

        # 3. Mode Description
        self.mode_label = QLabel("Glide 1 finger to write like a tablet")
        self.mode_label.setStyleSheet("color: #6B7280; font-size: 11px;")
        layout.addWidget(self.mode_label)

        layout.addStretch()

        # 4. Stroke Counter
        self.stroke_label = QLabel("Strokes: 0")
        layout.addWidget(self.stroke_label)

        # 5. Canvas Coordinates
        self.coord_label = QLabel("X: 0, Y: 0")
        layout.addWidget(self.coord_label)

        # 6. Zoom Level
        self.zoom_label = QLabel("100%")
        layout.addWidget(self.zoom_label)

    def set_device(self, device_name: str, is_fallback: bool = False) -> None:
        """Update device badge name and color."""
        if "Tablet" in device_name:
            self.device_badge.setText(f"📱 {device_name}")
            self.device_badge.setStyleSheet(
                "font-weight: 700; padding: 2px 8px; border-radius: 4px; background: rgba(37, 99, 235, 0.15); color: #2563EB;"
            )
        elif is_fallback:
            self.device_badge.setText(f"🟡 {device_name}")
            self.device_badge.setStyleSheet(
                "font-weight: 600; padding: 2px 8px; border-radius: 4px; background: rgba(234, 179, 8, 0.15); color: #CA8A04;"
            )
        else:
            self.device_badge.setText(f"🟢 {device_name}")
            self.device_badge.setStyleSheet(
                "font-weight: 600; padding: 2px 8px; border-radius: 4px; background: rgba(34, 197, 94, 0.15); color: #16A34A;"
            )

    def set_mode(self, mode_name: str) -> None:
        """Update mode description text."""
        self.mode_label.setText(mode_name)

    def set_inking(self, is_inking: bool) -> None:
        """Visually indicate active drawing in real-time."""
        if is_inking:
            self.inking_badge.setText("✍ Inking")
            self.inking_badge.setStyleSheet(
                "font-weight: 700; padding: 2px 8px; border-radius: 4px; background: rgba(59, 130, 246, 0.2); color: #2563EB;"
            )
        else:
            self.inking_badge.setText("○ Idle")
            self.inking_badge.setStyleSheet(
                "font-weight: 500; padding: 2px 8px; border-radius: 4px; background: rgba(156, 163, 175, 0.15); color: #6B7280;"
            )

    def set_coordinates(self, x: float, y: float) -> None:
        """Update coordinate readout."""
        self.coord_label.setText(f"X: {int(x)}, Y: {int(y)}")

    def set_stroke_count(self, count: int) -> None:
        """Update stroke count."""
        self.stroke_label.setText(f"Strokes: {count}")

    def set_zoom(self, zoom: float) -> None:
        """Update zoom percentage."""
        self.zoom_label.setText(f"{int(round(zoom * 100))}%")
