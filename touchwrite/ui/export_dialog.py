"""
Export options dialog for TouchWrite notebooks (PNG, PDF, SVG).
"""

from typing import Optional
import os
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QPushButton,
    QFileDialog,
    QLabel,
    QWidget,
)
from PySide6.QtCore import Qt


class ExportDialog(QDialog):
    """Dialog allowing user to choose export format and rendering options."""

    def __init__(self, default_filename: str = "notebook", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.default_filename = default_filename
        self.selected_format: str = "png"
        self.selected_filepath: str = ""
        self.include_background: bool = True
        self.transparent_bg: bool = False
        self.scale: float = 1.0
        self.crop_to_content: bool = False

        self.setWindowTitle("Export Handwriting")
        self.resize(480, 420)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # 1. Format Selection
        fmt_group = QGroupBox("Export Format")
        fmt_layout = QVBoxLayout(fmt_group)

        self.fmt_btn_group = QButtonGroup(self)

        self.rb_png = QRadioButton("PNG Image (.png) — Ideal for sharing, web, and notes")
        self.rb_png.setChecked(True)
        self.rb_pdf = QRadioButton("PDF Document (.pdf) — 300 DPI vector printable notebook page")
        self.rb_svg = QRadioButton("SVG Vector (.svg) — Infinite resolution vector graphics")

        self.fmt_btn_group.addButton(self.rb_png)
        self.fmt_btn_group.addButton(self.rb_pdf)
        self.fmt_btn_group.addButton(self.rb_svg)

        fmt_layout.addWidget(self.rb_png)
        fmt_layout.addWidget(self.rb_pdf)
        fmt_layout.addWidget(self.rb_svg)

        self.rb_png.toggled.connect(self._on_format_changed)
        self.rb_pdf.toggled.connect(self._on_format_changed)
        self.rb_svg.toggled.connect(self._on_format_changed)

        layout.addWidget(fmt_group)

        # 2. Options Group
        self.opt_group = QGroupBox("Rendering Options")
        opt_layout = QFormLayout(self.opt_group)

        self.chk_bg = QCheckBox("Include notebook paper background (ruled / grid)")
        self.chk_bg.setChecked(True)
        opt_layout.addRow("", self.chk_bg)

        self.chk_trans = QCheckBox("Transparent background (PNG only)")
        self.chk_trans.setChecked(False)
        self.chk_trans.toggled.connect(self._on_trans_toggled)
        opt_layout.addRow("", self.chk_trans)

        self.chk_crop = QCheckBox("Crop to content (trim empty borders)")
        self.chk_crop.setChecked(False)
        opt_layout.addRow("", self.chk_crop)

        self.combo_scale = QComboBox()
        self.combo_scale.addItem("Standard Resolution (1x)", 1.0)
        self.combo_scale.addItem("High-Definition Retina (2x)", 2.0)
        self.combo_scale.addItem("Ultra-Sharp Print (3x)", 3.0)
        opt_layout.addRow("Image Resolution:", self.combo_scale)

        layout.addWidget(self.opt_group)

        layout.addStretch()

        # 3. Actions
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_export = QPushButton("Choose File & Export...")
        btn_export.setDefault(True)
        btn_export.clicked.connect(self._choose_and_export)
        btn_box.addWidget(btn_export)

        layout.addLayout(btn_box)

    def _on_format_changed(self) -> None:
        if self.rb_png.isChecked():
            self.selected_format = "png"
            self.chk_trans.setEnabled(True)
            self.combo_scale.setEnabled(True)
            self.chk_crop.setEnabled(True)
        elif self.rb_pdf.isChecked():
            self.selected_format = "pdf"
            self.chk_trans.setEnabled(False)
            self.combo_scale.setEnabled(False)
            self.chk_crop.setEnabled(False)
        elif self.rb_svg.isChecked():
            self.selected_format = "svg"
            self.chk_trans.setEnabled(False)
            self.combo_scale.setEnabled(False)
            self.chk_crop.setEnabled(False)

    def _on_trans_toggled(self, checked: bool) -> None:
        if checked:
            self.chk_bg.setChecked(False)
            self.chk_bg.setEnabled(False)
        else:
            self.chk_bg.setEnabled(True)

    def _choose_and_export(self) -> None:
        ext = self.selected_format
        filter_str = f"{ext.upper()} Files (*.{ext})"

        default_path = os.path.join(os.path.expanduser("~"), f"{self.default_filename}.{ext}")
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            f"Export as {ext.upper()}",
            default_path,
            filter_str,
        )

        if filepath:
            if not filepath.lower().endswith(f".{ext.lower()}"):
                filepath += f".{ext.lower()}"
            self.selected_filepath = filepath
            self.include_background = self.chk_bg.isChecked()
            self.transparent_bg = self.chk_trans.isChecked()
            self.scale = self.combo_scale.currentData()
            self.crop_to_content = self.chk_crop.isChecked()
            self.accept()
