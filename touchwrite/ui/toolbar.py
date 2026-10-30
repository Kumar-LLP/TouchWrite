"""
Modern minimalist toolbar for TouchWrite notebook application.
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QToolBar,
    QToolButton,
    QWidget,
    QHBoxLayout,
    QLabel,
    QSlider,
    QComboBox,
    QColorDialog,
    QButtonGroup,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QPainter, QBrush, QPen

from touchwrite.config import AppConfig, ToolMode, PaperStyle, InputMode


class ColorSwatchButton(QToolButton):
    """Circular color swatch button with active indicator."""

    def __init__(self, color_hex: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.color_hex = color_hex
        self.setFixedSize(26, 26)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"Ink Color: {color_hex}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect()
        color = QColor(self.color_hex)

        # Draw outer selection ring if checked
        if self.isChecked():
            painter.setPen(QPen(QColor("#6366F1"), 2.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(rect.adjusted(1, 1, -1, -1))
            inner_rect = rect.adjusted(3, 3, -3, -3)
        else:
            painter.setPen(QPen(QColor(0, 0, 0, 30), 1.0))
            inner_rect = rect.adjusted(2, 2, -2, -2)

        # Draw color circle
        painter.setBrush(QBrush(color))
        painter.drawEllipse(inner_rect)


class SizePreviewWidget(QWidget):
    """Small widget visually displaying current pen dot size."""

    def __init__(self, size: float = 3.0, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.size_val = size
        self.setFixedSize(24, 24)

    def set_size(self, size: float) -> None:
        self.size_val = size
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        center = self.rect().center()
        r = max(1.0, min(10.0, self.size_val / 2.0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#1F2937")))
        painter.drawEllipse(center, r, r)


class TouchWriteToolBar(QToolBar):
    """Main application toolbar holding drawing tools, palette, and actions."""

    # Signals
    tablet_mode_toggled = Signal(bool)
    tool_changed = Signal(ToolMode)
    pen_size_changed = Signal(float)
    pen_color_changed = Signal(str)
    paper_style_changed = Signal(PaperStyle)
    input_mode_changed = Signal(InputMode)
    undo_requested = Signal()
    redo_requested = Signal()
    clear_requested = Signal()
    save_requested = Signal()
    export_requested = Signal()
    calibration_requested = Signal()
    settings_requested = Signal()
    theme_toggle_requested = Signal()

    def __init__(self, config: Optional[AppConfig] = None, parent: Optional[QWidget] = None):
        super().__init__("Main Tools", parent)
        self.config = config or AppConfig()
        self.setMovable(False)
        self.setIconSize(QSize(20, 20))

        self._build_ui()

    def _build_ui(self) -> None:
        # 0. Primary 2-Finger Tablet Mode Button (Prominent toggle)
        self.btn_tablet_mode = QToolButton()
        self.btn_tablet_mode.setCheckable(True)
        self.btn_tablet_mode.setChecked(self.config.tablet_touchpad_mode)
        self._update_tablet_button_text()
        self.btn_tablet_mode.setToolTip(
            "Toggle 2-Finger Tablet Mode (T)\n"
            "• 1 Finger: Normal Mouse Pointer\n"
            "• 2 Fingers: Write in Ink (Tablet Mode)\n"
            "• 3 Fingers: Scroll / Pan Page\n"
            "• External Mouse: Normal Mouse"
        )
        self.btn_tablet_mode.clicked.connect(self._on_tablet_btn_clicked)
        self.addWidget(self.btn_tablet_mode)

        self.addSeparator()

        # Tool button group (Pen vs Eraser)
        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)

        # 1. Pen Tool Button
        self.btn_pen = QToolButton()
        self.btn_pen.setText("✏ Pen")
        self.btn_pen.setCheckable(True)
        self.btn_pen.setChecked(True)
        self.btn_pen.setToolTip("Pen Tool (B) — Write with smooth natural ink")
        self.btn_pen.clicked.connect(lambda: self.tool_changed.emit(ToolMode.PEN))
        self.tool_group.addButton(self.btn_pen)
        self.addWidget(self.btn_pen)

        # 2. Eraser Tool Button
        self.btn_eraser = QToolButton()
        self.btn_eraser.setText("⌫ Eraser")
        self.btn_eraser.setCheckable(True)
        self.btn_eraser.setToolTip("Eraser Tool (E) — Touch strokes to erase")
        self.btn_eraser.clicked.connect(lambda: self.tool_changed.emit(ToolMode.ERASER))
        self.tool_group.addButton(self.btn_eraser)
        self.addWidget(self.btn_eraser)

        self.addSeparator()

        # 3. Pen Size Slider and Indicator
        size_container = QWidget()
        size_layout = QHBoxLayout(size_container)
        size_layout.setContentsMargins(4, 0, 4, 0)
        size_layout.setSpacing(6)

        self.size_preview = SizePreviewWidget(self.config.pen_width)
        size_layout.addWidget(self.size_preview)

        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(1, 16)
        self.size_slider.setValue(int(self.config.pen_width))
        self.size_slider.setFixedWidth(70)
        self.size_slider.setToolTip("Adjust Pen Stroke Width")
        self.size_slider.valueChanged.connect(self._on_size_slider_changed)
        size_layout.addWidget(self.size_slider)

        self.addWidget(size_container)

        self.addSeparator()

        # 4. Color Swatches
        color_container = QWidget()
        color_layout = QHBoxLayout(color_container)
        color_layout.setContentsMargins(4, 0, 4, 0)
        color_layout.setSpacing(4)

        self.color_group = QButtonGroup(self)
        self.color_group.setExclusive(True)
        self.swatch_buttons: List[ColorSwatchButton] = []

        for col in self.config.color_palette:
            swatch = ColorSwatchButton(col)
            if col.upper() == self.config.pen_color.upper():
                swatch.setChecked(True)
            swatch.clicked.connect(lambda checked, c=col: self._select_color(c))
            self.color_group.addButton(swatch)
            color_layout.addWidget(swatch)
            self.swatch_buttons.append(swatch)

        # Custom color picker button
        self.btn_custom_color = QToolButton()
        self.btn_custom_color.setText("🎨")
        self.btn_custom_color.setToolTip("Pick Custom Color...")
        self.btn_custom_color.clicked.connect(self._open_color_picker)
        color_layout.addWidget(self.btn_custom_color)

        self.addWidget(color_container)

        self.addSeparator()

        # 5. Paper Style Selector
        self.paper_combo = QComboBox()
        self.paper_combo.addItem("📄 Ruled Paper", PaperStyle.RULED)
        self.paper_combo.addItem("▦ Grid Paper", PaperStyle.GRID)
        self.paper_combo.addItem("⬜ Blank Paper", PaperStyle.BLANK)
        self.paper_combo.setToolTip("Select Notebook Paper Background")
        self.paper_combo.currentIndexChanged.connect(self._on_paper_changed)
        self.addWidget(self.paper_combo)

        # 6. Input Mode Selector
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("📱 Single-Finger Tablet Mode", InputMode.TABLET_TOUCHPAD)
        self.mode_combo.addItem("⚡ Hold Space to Write", InputMode.HOLD_TO_WRITE)
        self.mode_combo.addItem("🖐 Direct Touch Inking", InputMode.DIRECT_CONTACT)
        self.mode_combo.addItem("⏱ Auto-Lift Dwell", InputMode.AUTO_DWELL)
        self.mode_combo.addItem("🖱 Click / Tap to Write", InputMode.CLICK_AND_DRAG)
        self.mode_combo.setToolTip("Configure Touchpad Finger Inking Mode")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.addWidget(self.mode_combo)

        self.addSeparator()

        # 7. Undo & Redo
        self.btn_undo = QToolButton()
        self.btn_undo.setText("↩ Undo")
        self.btn_undo.setEnabled(False)
        self.btn_undo.setToolTip("Undo (Ctrl+Z)")
        self.btn_undo.clicked.connect(self.undo_requested.emit)
        self.addWidget(self.btn_undo)

        self.btn_redo = QToolButton()
        self.btn_redo.setText("↪ Redo")
        self.btn_redo.setEnabled(False)
        self.btn_redo.setToolTip("Redo (Ctrl+Y)")
        self.btn_redo.clicked.connect(self.redo_requested.emit)
        self.addWidget(self.btn_redo)

        # 8. Clear Page
        self.btn_clear = QToolButton()
        self.btn_clear.setText("🗑 Clear")
        self.btn_clear.setToolTip("Clear Page (Ctrl+L)")
        self.btn_clear.clicked.connect(self.clear_requested.emit)
        self.addWidget(self.btn_clear)

        self.addSeparator()

        # 9. Calibration & Diagnostics
        self.btn_calibrate = QToolButton()
        self.btn_calibrate.setText("🔍 Calibrate / Test")
        self.btn_calibrate.setToolTip("Touchpad Input Test & Hardware Calibration (F1)")
        self.btn_calibrate.clicked.connect(self.calibration_requested.emit)
        self.addWidget(self.btn_calibrate)

        # 10. Save & Export & Settings
        self.btn_save = QToolButton()
        self.btn_save.setText("💾 Save")
        self.btn_save.setToolTip("Save Session (Ctrl+S)")
        self.btn_save.clicked.connect(self.save_requested.emit)
        self.addWidget(self.btn_save)

        self.btn_export = QToolButton()
        self.btn_export.setText("📤 Export")
        self.btn_export.setToolTip("Export as PNG / PDF / SVG (Ctrl+E)")
        self.btn_export.clicked.connect(self.export_requested.emit)
        self.addWidget(self.btn_export)

        self.btn_settings = QToolButton()
        self.btn_settings.setText("⚙ Settings")
        self.btn_settings.setToolTip("Preferences & Settings (Ctrl+,)")
        self.btn_settings.clicked.connect(self.settings_requested.emit)
        self.addWidget(self.btn_settings)

        # 11. Theme Toggle
        self.btn_theme = QToolButton()
        self.btn_theme.setText("🌓")
        self.btn_theme.setToolTip("Toggle Dark / Light Theme")
        self.btn_theme.clicked.connect(self.theme_toggle_requested.emit)
        self.addWidget(self.btn_theme)

    def _on_tablet_btn_clicked(self) -> None:
        enabled = self.btn_tablet_mode.isChecked()
        self.config.tablet_touchpad_mode = enabled
        self._update_tablet_button_text()
        self.tablet_mode_toggled.emit(enabled)

    def _update_tablet_button_text(self) -> None:
        if self.config.tablet_touchpad_mode:
            self.btn_tablet_mode.setText("✌️ 2-Finger Tablet: ON")
            self.btn_tablet_mode.setStyleSheet(
                "background-color: #2563EB; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 5px 10px;"
            )
        else:
            self.btn_tablet_mode.setText("✌️ 2-Finger Tablet: OFF")
            self.btn_tablet_mode.setStyleSheet(
                "background-color: #E5E7EB; color: #4B5563; font-weight: 500; border-radius: 6px; padding: 5px 10px;"
            )

    def set_tablet_mode_state(self, enabled: bool) -> None:
        """Update tablet button checked state and appearance."""
        self.btn_tablet_mode.blockSignals(True)
        self.btn_tablet_mode.setChecked(enabled)
        self.config.tablet_touchpad_mode = enabled
        self._update_tablet_button_text()
        self.btn_tablet_mode.blockSignals(False)

    def _on_size_slider_changed(self, value: int) -> None:
        self.size_preview.set_size(float(value))
        self.pen_size_changed.emit(float(value))

    def _select_color(self, color_hex: str) -> None:
        self.pen_color_changed.emit(color_hex)

    def _open_color_picker(self) -> None:
        color = QColorDialog.getColor(QColor(self.config.pen_color), self, "Select Ink Color")
        if color.isValid():
            hex_val = color.name().upper()
            self.pen_color_changed.emit(hex_val)

    def _on_paper_changed(self, index: int) -> None:
        style = self.paper_combo.itemData(index)
        if style:
            self.paper_style_changed.emit(style)

    def _on_mode_changed(self, index: int) -> None:
        mode = self.mode_combo.itemData(index)
        if mode:
            self.input_mode_changed.emit(mode)

    def update_history_state(self, can_undo: bool, can_redo: bool) -> None:
        """Update enabled state of undo and redo buttons."""
        self.btn_undo.setEnabled(can_undo)
        self.btn_redo.setEnabled(can_redo)

    def set_active_tool(self, tool: ToolMode) -> None:
        """Programmatically switch active tool button."""
        if tool == ToolMode.PEN:
            self.btn_pen.setChecked(True)
        elif tool == ToolMode.ERASER:
            self.btn_eraser.setChecked(True)

    def set_paper_style(self, style: PaperStyle) -> None:
        """Update paper style combo box."""
        idx = self.paper_combo.findData(style)
        if idx >= 0:
            self.paper_combo.blockSignals(True)
            self.paper_combo.setCurrentIndex(idx)
            self.paper_combo.blockSignals(False)

    def set_input_mode(self, mode: InputMode) -> None:
        """Update input mode combo box."""
        idx = self.mode_combo.findData(mode)
        if idx >= 0:
            self.mode_combo.blockSignals(True)
            self.mode_combo.setCurrentIndex(idx)
            self.mode_combo.blockSignals(False)

    def set_pen_size(self, size: float) -> None:
        """Update pen size slider and preview."""
        self.size_slider.blockSignals(True)
        self.size_slider.setValue(int(size))
        self.size_slider.blockSignals(False)
        self.size_preview.set_size(size)

    def set_pen_color(self, color_hex: str) -> None:
        """Update active color swatch button."""
        self.config.pen_color = color_hex
        for swatch in self.swatch_buttons:
            if swatch.color_hex.upper() == color_hex.upper():
                swatch.setChecked(True)
                break
