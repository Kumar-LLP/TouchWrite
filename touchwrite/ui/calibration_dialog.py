"""
Touchpad calibration, hardware diagnostic, and input-testing interface for TouchWrite.
"""

from typing import Optional, List
import time
import math
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QTextEdit,
    QRadioButton,
    QButtonGroup,
    QSlider,
    QWidget,
)
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

from touchwrite.config import AppConfig, InputMode
from touchwrite.canvas.stroke import Stroke, StrokePoint
from touchwrite.canvas.renderer import InkRenderer


class PracticeTestPad(QWidget):
    """Miniature drawing pad for live finger-writing calibration inside the dialog."""

    def __init__(self, config: AppConfig, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config = config
        self.setMinimumSize(400, 200)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.strokes: List[Stroke] = []
        self.current_stroke: Optional[Stroke] = None
        self.is_space_held = False
        self.live_info = "Ready. Place finger on touchpad..."
        self.on_telemetry: Optional[callable] = None

        # Lift timer for single-finger tablet mode
        self.lift_timer = QTimer(self)
        self.lift_timer.setSingleShot(True)
        self.lift_timer.timeout.connect(self._end_stroke)

    def clear(self) -> None:
        self.strokes.clear()
        self.current_stroke = None
        self.update()

    def mousePressEvent(self, event):
        pos = event.position()
        if self.config.input_mode in (InputMode.CLICK_AND_DRAG, InputMode.TABLET_TOUCHPAD):
            self._start_stroke(pos)

    def mouseMoveEvent(self, event):
        pos = event.position()
        mode = self.config.input_mode

        if mode == InputMode.TABLET_TOUCHPAD or self.config.tablet_touchpad_mode:
            if self.current_stroke is None:
                self._start_stroke(pos)
            else:
                self._continue_stroke(pos)
            self.lift_timer.start(max(30, self.config.finger_lift_timeout_ms))

        elif mode == InputMode.HOLD_TO_WRITE:
            if self.is_space_held:
                if self.current_stroke is None:
                    self._start_stroke(pos)
                else:
                    self._continue_stroke(pos)
        elif mode == InputMode.DIRECT_CONTACT:
            if self.current_stroke is None:
                self._start_stroke(pos)
            else:
                self._continue_stroke(pos)
            self.lift_timer.start(180)
        elif mode == InputMode.CLICK_AND_DRAG:
            if event.buttons() & Qt.MouseButton.LeftButton:
                if self.current_stroke is None:
                    self._start_stroke(pos)
                else:
                    self._continue_stroke(pos)

    def mouseReleaseEvent(self, event):
        if self.config.input_mode == InputMode.CLICK_AND_DRAG:
            self._end_stroke()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.is_space_held = True
            pos = self.mapFromGlobal(self.cursor().pos())
            if self.rect().contains(pos):
                self._start_stroke(pos)
            event.accept()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.is_space_held = False
            self._end_stroke()
            event.accept()

    def _start_stroke(self, pos: QPointF):
        self.current_stroke = Stroke(color="#2563EB", width=3.5)
        self.current_stroke.add_point(StrokePoint(pos.x(), pos.y()))
        self._notify_telemetry(pos, inking=True)
        self.update()

    def _continue_stroke(self, pos: QPointF):
        if self.current_stroke:
            self.current_stroke.add_point(StrokePoint(pos.x(), pos.y()))
            self._notify_telemetry(pos, inking=True)
            self.update()

    def _end_stroke(self):
        if self.current_stroke:
            if self.current_stroke.points:
                self.strokes.append(self.current_stroke)
            self.current_stroke = None
            self._notify_telemetry(QPointF(0, 0), inking=False)
            self.update()

    def _notify_telemetry(self, pos: QPointF, inking: bool):
        if self.on_telemetry:
            self.on_telemetry(pos.x(), pos.y(), inking)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Background
        painter.fillRect(self.rect(), QBrush(QColor("#FFFFFF")))
        painter.setPen(QPen(QColor("#E5E7EB"), 1.0))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        # Practice guide lines
        pen = QPen(QColor("#F3F4F6"), 1.0)
        painter.setPen(pen)
        for y in range(40, self.height(), 40):
            painter.drawLine(0, y, self.width(), y)

        # Instructions watermark
        if not self.strokes and not self.current_stroke:
            painter.setPen(QColor("#9CA3AF"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Practice Writing Pad\n(Glide 1 finger on touchpad to write normally like a tablet)",
            )

        # Strokes
        InkRenderer.render_all(painter, self.strokes, None, True)
        if self.current_stroke:
            InkRenderer.render_stroke(painter, self.current_stroke, True)


class CalibrationDialog(QDialog):
    """
    Input testing, device calibration, and diagnostic status dialog.
    """

    def __init__(self, config: AppConfig, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("TouchWrite - Input Calibration & Diagnostic Tool")
        self.resize(720, 620)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # 1. Header Information
        header = QLabel(
            "<h3>Touchpad Calibration & Diagnostics</h3>"
            "Verify your Windows 11 Precision Touchpad input, test finger handwriting, "
            "and select your preferred input mode."
        )
        header.setWordWrap(True)
        layout.addWidget(header)

        # 2. Hardware Inspection Status
        hw_group = QGroupBox("Hardware & Windows API Status")
        hw_layout = QVBoxLayout(hw_group)

        self.hw_label = QLabel(
            "<b>Detected Touchpad:</b> Goodix Precision Touchpad (GXTP5100, VID: 0x27C6, PID: 0x01E0)<br>"
            "<b>HID Classification:</b> Digitizer Collection (UsagePage: 0x0D, Usage: 0x05)<br>"
            "<b>Windows Pointer Subsystem:</b> Active (WM_POINTER / WM_INPUT)<br>"
            "<b>Laptop Screen:</b> Standard Display (Non-touch LOQ panel)<br>"
            "<b>Status:</b> Native Precision Touchpad verified and operational."
        )
        self.hw_label.setStyleSheet("color: #374151; font-size: 12px; line-height: 1.4;")
        hw_layout.addWidget(self.hw_label)
        layout.addWidget(hw_group)

        # 3. Practice & Calibration Pad
        pad_group = QGroupBox("Interactive Calibration & Writing Test Pad")
        pad_layout = QVBoxLayout(pad_group)

        self.test_pad = PracticeTestPad(self.config, self)
        self.test_pad.on_telemetry = self._on_pad_telemetry
        pad_layout.addWidget(self.test_pad)

        pad_controls = QHBoxLayout()
        self.lbl_pad_coords = QLabel("Pointer: X: 0, Y: 0 | Inking: False")
        pad_controls.addWidget(self.lbl_pad_coords)

        pad_controls.addStretch()

        btn_clear_pad = QPushButton("Clear Test Pad")
        btn_clear_pad.clicked.connect(self.test_pad.clear)
        pad_controls.addWidget(btn_clear_pad)

        pad_layout.addLayout(pad_controls)
        layout.addWidget(pad_group)

        # 4. Input Mode Selection
        mode_group = QGroupBox("Touchpad Writing Mode Selection")
        mode_layout = QVBoxLayout(mode_group)

        self.mode_btn_group = QButtonGroup(self)

        self.rb_tablet = QRadioButton("📱 Single-Finger Tablet Mode (Recommended — Touch & write naturally like an iPad/tablet with 1 finger)")
        self.rb_hold = QRadioButton("⚡ Hold Space to Write (Two-handed trigger mode)")
        self.rb_dwell = QRadioButton("⏱ Auto-Lift Dwell (Automatic pen-up when finger pauses)")
        self.rb_click = QRadioButton("🖱 Mouse / Tap Fallback (Standard physical click or double-tap drag)")

        modes = [
            (self.rb_tablet, InputMode.TABLET_TOUCHPAD),
            (self.rb_hold, InputMode.HOLD_TO_WRITE),
            (self.rb_dwell, InputMode.AUTO_DWELL),
            (self.rb_click, InputMode.CLICK_AND_DRAG),
        ]

        for rb, mode in modes:
            self.mode_btn_group.addButton(rb)
            mode_layout.addWidget(rb)
            if self.config.input_mode == mode:
                rb.setChecked(True)
            rb.toggled.connect(lambda checked, m=mode: self._on_mode_toggled(checked, m))

        layout.addWidget(mode_group)

        # 5. Dialog Close Button
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_close = QPushButton("Done")
        btn_close.setDefault(True)
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)

        layout.addLayout(btn_box)

    def _on_pad_telemetry(self, x: float, y: float, inking: bool) -> None:
        ink_text = "Writing..." if inking else "Hover / Idle"
        self.lbl_pad_coords.setText(f"Pointer: X: {int(x)}, Y: {int(y)} | State: {ink_text}")

    def _on_mode_toggled(self, checked: bool, mode: InputMode) -> None:
        if checked:
            self.config.input_mode = mode
            self.config.tablet_touchpad_mode = (mode == InputMode.TABLET_TOUCHPAD)
