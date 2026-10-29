"""
Application preferences and settings dialog for TouchWrite.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
    QComboBox,
    QPushButton,
    QWidget,
)
from PySide6.QtCore import Qt

from touchwrite.config import AppConfig, PaperStyle, InputMode


class SettingsDialog(QDialog):
    """Configuration dialog for tuning pen dynamics, paper layout, and input modes."""

    def __init__(self, config: AppConfig, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("TouchWrite Settings")
        self.resize(520, 540)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # 1. Pen Dynamics Group
        pen_group = QGroupBox("Pen & Ink Dynamics")
        pen_layout = QFormLayout(pen_group)

        self.spin_pen_width = QDoubleSpinBox()
        self.spin_pen_width.setRange(0.5, 30.0)
        self.spin_pen_width.setSingleStep(0.5)
        self.spin_pen_width.setValue(self.config.pen_width)
        pen_layout.addRow("Default Pen Thickness (pt):", self.spin_pen_width)

        self.chk_pressure = QCheckBox("Enable natural velocity-based pressure variation")
        self.chk_pressure.setChecked(self.config.pressure_simulation)
        pen_layout.addRow("", self.chk_pressure)

        layout.addWidget(pen_group)

        # 2. Eraser Settings Group
        eraser_group = QGroupBox("Eraser Configuration")
        eraser_layout = QFormLayout(eraser_group)

        self.spin_eraser_width = QDoubleSpinBox()
        self.spin_eraser_width.setRange(5.0, 100.0)
        self.spin_eraser_width.setValue(self.config.eraser_width)
        eraser_layout.addRow("Eraser Reach / Radius (px):", self.spin_eraser_width)

        self.chk_stroke_eraser = QCheckBox("Stroke Eraser (Erase entire strokes on touch)")
        self.chk_stroke_eraser.setChecked(self.config.stroke_eraser)
        eraser_layout.addRow("", self.chk_stroke_eraser)

        layout.addWidget(eraser_group)

        # 3. Paper Background & Margins
        paper_group = QGroupBox("Notebook Paper Settings")
        paper_layout = QFormLayout(paper_group)

        self.combo_paper = QComboBox()
        self.combo_paper.addItem("Ruled / Lined Paper", PaperStyle.RULED)
        self.combo_paper.addItem("Grid / Graph Paper", PaperStyle.GRID)
        self.combo_paper.addItem("Blank Paper", PaperStyle.BLANK)
        idx = self.combo_paper.findData(self.config.paper_style)
        if idx >= 0:
            self.combo_paper.setCurrentIndex(idx)
        paper_layout.addRow("Default Paper Background:", self.combo_paper)

        self.spin_line_spacing = QSpinBox()
        self.spin_line_spacing.setRange(15, 100)
        self.spin_line_spacing.setValue(self.config.paper_line_spacing)
        paper_layout.addRow("Line Spacing (px):", self.spin_line_spacing)

        self.spin_margin = QSpinBox()
        self.spin_margin.setRange(0, 300)
        self.spin_margin.setValue(self.config.paper_margin)
        paper_layout.addRow("Left Margin Line Position (px):", self.spin_margin)

        layout.addWidget(paper_group)

        # 4. Touchpad & Input Tuning
        input_group = QGroupBox("Touchpad Tablet Tuning")
        input_layout = QFormLayout(input_group)

        self.spin_lift = QSpinBox()
        self.spin_lift.setRange(40, 300)
        self.spin_lift.setSingleStep(5)
        self.spin_lift.setSuffix(" ms")
        self.spin_lift.setValue(self.config.finger_lift_timeout_ms)
        input_layout.addRow("Tablet Mode Finger-Lift Sensitivity:", self.spin_lift)

        self.spin_dwell = QSpinBox()
        self.spin_dwell.setRange(50, 1000)
        self.spin_dwell.setSingleStep(25)
        self.spin_dwell.setSuffix(" ms")
        self.spin_dwell.setValue(self.config.dwell_timeout_ms)
        input_layout.addRow("Auto-Lift Dwell Timeout:", self.spin_dwell)

        layout.addWidget(input_group)

        layout.addStretch()

        # 5. Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Save Settings")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save_and_accept)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)

    def _save_and_accept(self) -> None:
        self.config.pen_width = self.spin_pen_width.value()
        self.config.pressure_simulation = self.chk_pressure.isChecked()
        self.config.eraser_width = self.spin_eraser_width.value()
        self.config.stroke_eraser = self.chk_stroke_eraser.isChecked()
        self.config.paper_style = self.combo_paper.currentData()
        self.config.paper_line_spacing = self.spin_line_spacing.value()
        self.config.paper_margin = self.spin_margin.value()
        self.config.dwell_timeout_ms = self.spin_dwell.value()
        self.config.finger_lift_timeout_ms = self.spin_lift.value()
        self.accept()
