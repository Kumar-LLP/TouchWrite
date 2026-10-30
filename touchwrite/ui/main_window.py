"""
Main desktop window for TouchWrite handwriting application.
"""

import sys
import os
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QFileDialog,
    QMenuBar,
    QMenu,
    QStatusBar,
    QApplication,
)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QAction, QKeySequence, QIcon

from touchwrite.config import AppConfig, ToolMode, PaperStyle, InputMode
from touchwrite.canvas.canvas import TouchCanvas
from touchwrite.input.manager import InputManager
from touchwrite.input.base import InputDeviceType
from touchwrite.storage.session_manager import SessionManager
from touchwrite.export.image_export import export_to_png
from touchwrite.export.svg_export import export_to_svg
from touchwrite.export.pdf_export import export_to_pdf
from touchwrite.ui.toolbar import TouchWriteToolBar
from touchwrite.ui.status_widget import StatusBarWidget
from touchwrite.ui.settings_dialog import SettingsDialog
from touchwrite.ui.calibration_dialog import CalibrationDialog
from touchwrite.ui.export_dialog import ExportDialog
from touchwrite.ui.theme import apply_theme


class MainWindow(QMainWindow):
    """
    Main desktop window assembling the notepad canvas, toolbar, input manager,
    status bar, and menus.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__()
        self.config = config or AppConfig()
        self.setWindowTitle("TouchWrite - Digital Notebook")
        self.resize(1200, 800)

        # 1. Instantiate Core Canvas
        self.canvas = TouchCanvas(self.config, self)
        self.setCentralWidget(self.canvas)

        # 2. Instantiate Input Manager
        self.input_manager = InputManager(self.config, self)
        self.input_manager.attach_canvas(self.canvas)

        # 3. Instantiate Session Manager
        self.session_manager = SessionManager(self.config, self)

        # 4. Build UI Subsystems
        self._build_toolbar()
        self._build_statusbar()
        self._build_menus()
        self._connect_signals()

        # Apply initial theme
        apply_theme(self, self.config.theme)

        # Enable Drag and Drop for session files
        self.setAcceptDrops(True)

        # Center on screen
        self._center_window()

    def showEvent(self, event):
        super().showEvent(event)
        # Register window handle with native pointer adapter
        hwnd = int(self.winId())
        self.input_manager.register_window_handle(hwnd)

    def _center_window(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move((geo.width() - self.width()) // 2, (geo.height() - self.height()) // 2)

    # -------------------------------------------------------------------------
    # UI Setup
    # -------------------------------------------------------------------------

    def _build_toolbar(self) -> None:
        self.toolbar = TouchWriteToolBar(self.config, self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

    def _build_statusbar(self) -> None:
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_widget = StatusBarWidget(self)
        self.status_bar.addWidget(self.status_widget, 1)

    def _build_menus(self) -> None:
        menubar = self.menuBar()

        # --- File Menu ---
        file_menu = menubar.addMenu("&File")

        act_new = QAction("&New Notebook", self)
        act_new.setShortcut(QKeySequence.StandardKey.New)
        act_new.triggered.connect(self._on_action_new)
        file_menu.addAction(act_new)

        act_open = QAction("&Open Session...", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.triggered.connect(self._on_action_open)
        file_menu.addAction(act_open)

        act_save = QAction("&Save", self)
        act_save.setShortcut(QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self._on_action_save)
        file_menu.addAction(act_save)

        act_save_as = QAction("Save &As...", self)
        act_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        act_save_as.triggered.connect(self._on_action_save_as)
        file_menu.addAction(act_save_as)

        file_menu.addSeparator()

        act_export = QAction("&Export Handwriting...", self)
        act_export.setShortcut(QKeySequence("Ctrl+E"))
        act_export.triggered.connect(self._on_action_export)
        file_menu.addAction(act_export)

        file_menu.addSeparator()

        act_exit = QAction("E&xit", self)
        act_exit.setShortcut(QKeySequence.StandardKey.Quit)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # --- Edit Menu ---
        edit_menu = menubar.addMenu("&Edit")

        self.act_undo = QAction("&Undo", self)
        self.act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.act_undo.setEnabled(False)
        self.act_undo.triggered.connect(self.canvas.undo)
        edit_menu.addAction(self.act_undo)

        self.act_redo = QAction("&Redo", self)
        self.act_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.act_redo.setEnabled(False)
        self.act_redo.triggered.connect(self.canvas.redo)
        edit_menu.addAction(self.act_redo)

        edit_menu.addSeparator()

        act_clear = QAction("&Clear Page", self)
        act_clear.setShortcut(QKeySequence("Ctrl+L"))
        act_clear.triggered.connect(self._on_action_clear)
        edit_menu.addAction(act_clear)

        # --- View Menu ---
        view_menu = menubar.addMenu("&View")

        act_zoom_in = QAction("Zoom &In", self)
        act_zoom_in.setShortcut(QKeySequence.StandardKey.ZoomIn)
        act_zoom_in.triggered.connect(self.canvas.zoom_in)
        view_menu.addAction(act_zoom_in)

        act_zoom_out = QAction("Zoom &Out", self)
        act_zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)
        act_zoom_out.triggered.connect(self.canvas.zoom_out)
        view_menu.addAction(act_zoom_out)

        act_reset_zoom = QAction("&Reset Zoom (100%)", self)
        act_reset_zoom.setShortcut(QKeySequence("Ctrl+0"))
        act_reset_zoom.triggered.connect(self.canvas.reset_view)
        view_menu.addAction(act_reset_zoom)

        act_fit_width = QAction("&Fit Page Width", self)
        act_fit_width.triggered.connect(self.canvas.fit_page_width)
        view_menu.addAction(act_fit_width)

        view_menu.addSeparator()

        act_theme = QAction("Toggle &Dark/Light Theme", self)
        act_theme.triggered.connect(self._toggle_theme)
        view_menu.addAction(act_theme)

        # --- Tools Menu ---
        tools_menu = menubar.addMenu("&Tools")

        act_pen = QAction("&Pen Tool", self)
        act_pen.setShortcut(QKeySequence("B"))
        act_pen.triggered.connect(lambda: self._set_tool(ToolMode.PEN))
        tools_menu.addAction(act_pen)

        act_eraser = QAction("&Eraser Tool", self)
        act_eraser.setShortcut(QKeySequence("E"))
        act_eraser.triggered.connect(lambda: self._set_tool(ToolMode.ERASER))
        tools_menu.addAction(act_eraser)

        tools_menu.addSeparator()

        act_calibrate = QAction("Touchpad &Calibration / Test...", self)
        act_calibrate.setShortcut(QKeySequence("F1"))
        act_calibrate.triggered.connect(self._open_calibration_dialog)
        tools_menu.addAction(act_calibrate)

        act_settings = QAction("&Preferences...", self)
        act_settings.setShortcut(QKeySequence("Ctrl+,"))
        act_settings.triggered.connect(self._open_settings_dialog)
        tools_menu.addAction(act_settings)

        # --- Help Menu ---
        help_menu = menubar.addMenu("&Help")

        act_guide = QAction("Touchpad Handwriting &Guide", self)
        act_guide.triggered.connect(self._show_guide)
        help_menu.addAction(act_guide)

        act_about = QAction("&About TouchWrite", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    # -------------------------------------------------------------------------
    # Signal Connections
    # -------------------------------------------------------------------------

    def _connect_signals(self) -> None:
        # Canvas signals -> Status Bar & UI
        self.canvas.inking_changed.connect(self.status_widget.set_inking)
        self.canvas.cursor_moved.connect(self.status_widget.set_coordinates)
        self.canvas.stroke_count_changed.connect(self._on_stroke_count_changed)
        self.canvas.history_changed.connect(self._on_history_changed)
        self.canvas.zoom_changed.connect(self.status_widget.set_zoom)

        # Toolbar signals -> Canvas & Settings
        self.toolbar.tablet_mode_toggled.connect(self._on_tablet_mode_toggled)
        self.toolbar.tool_changed.connect(self.canvas.set_tool)
        self.toolbar.pen_size_changed.connect(self.canvas.set_pen_width)
        self.toolbar.pen_color_changed.connect(self.canvas.set_pen_color)
        self.toolbar.paper_style_changed.connect(self.canvas.set_paper_style)
        self.toolbar.input_mode_changed.connect(self._on_input_mode_changed)

        self.toolbar.undo_requested.connect(self.canvas.undo)
        self.toolbar.redo_requested.connect(self.canvas.redo)
        self.toolbar.clear_requested.connect(self._on_action_clear)
        self.toolbar.save_requested.connect(self._on_action_save)
        self.toolbar.export_requested.connect(self._on_action_export)
        self.toolbar.calibration_requested.connect(self._open_calibration_dialog)
        self.toolbar.settings_requested.connect(self._open_settings_dialog)
        self.toolbar.theme_toggle_requested.connect(self._toggle_theme)

        # Input Manager -> Status Bar
        self.input_manager.device_changed.connect(lambda name: self.status_widget.set_device(name))
        self.input_manager.mode_changed.connect(lambda name: self.status_widget.set_mode(name))

        # Session Manager -> Window Title
        self.session_manager.title_changed.connect(self.setWindowTitle)

    # -------------------------------------------------------------------------
    # Event Pipeline Routing (Keyboard & Native Events)
    # -------------------------------------------------------------------------

    def keyPressEvent(self, event) -> None:
        # Quick toggle key 'T' for Single-Finger Tablet Mode
        if event.key() == Qt.Key.Key_T and not event.isAutoRepeat() and not (event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)):
            new_state = self.input_manager.toggle_tablet_mode()
            self.toolbar.set_tablet_mode_state(new_state)
            self.status_widget.set_device(self.input_manager.get_active_device_label())
            self.status_widget.set_mode(self.input_manager.get_active_mode_label())
            self.toolbar.set_input_mode(self.config.input_mode)
            event.accept()
            return

        # Route to input manager first for Hold-to-Write mode
        if self.input_manager.dispatch_key_press(event):
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event) -> None:
        if self.input_manager.dispatch_key_release(event):
            event.accept()
            return
        super().keyReleaseEvent(event)

    def nativeEvent(self, eventType, message):
        self.input_manager.dispatch_native_event(eventType, message)
        return super().nativeEvent(eventType, message)

    # -------------------------------------------------------------------------
    # UI Actions & Handlers
    # -------------------------------------------------------------------------

    def _set_tool(self, tool: ToolMode) -> None:
        self.canvas.set_tool(tool)
        self.toolbar.set_active_tool(tool)

    def _on_stroke_count_changed(self, count: int) -> None:
        self.status_widget.set_stroke_count(count)
        self.session_manager.set_dirty(True)

    def _on_history_changed(self, can_undo: bool, can_redo: bool) -> None:
        self.toolbar.update_history_state(can_undo, can_redo)
        self.act_undo.setEnabled(can_undo)
        self.act_redo.setEnabled(can_redo)

    def _on_tablet_mode_toggled(self, enabled: bool) -> None:
        """Handle toggle of single-finger tablet touchpad mode."""
        self.input_manager.toggle_tablet_mode(enabled)
        self.status_widget.set_device(self.input_manager.get_active_device_label())
        self.status_widget.set_mode(self.input_manager.get_active_mode_label())
        self.toolbar.set_input_mode(self.config.input_mode)

    def _on_input_mode_changed(self, mode: InputMode) -> None:
        self.input_manager.set_input_mode(mode)
        is_tablet = (mode == InputMode.TABLET_TOUCHPAD)
        self.toolbar.set_tablet_mode_state(is_tablet)

    def _toggle_theme(self) -> None:
        self.config.theme = "dark" if self.config.theme == "light" else "light"
        apply_theme(self, self.config.theme)
        self.canvas.update()

    def _open_calibration_dialog(self) -> None:
        dlg = CalibrationDialog(self.config, self)
        dlg.exec()
        # Synchronize status bar and toolbar mode dropdown
        self.status_widget.set_mode(self.input_manager.get_active_mode_label())
        self.toolbar.set_input_mode(self.config.input_mode)

    def _open_settings_dialog(self) -> None:
        dlg = SettingsDialog(self.config, self)
        if dlg.exec():
            self.canvas.set_pen_width(self.config.pen_width)
            self.canvas.set_paper_style(self.config.paper_style)
            self.toolbar.set_pen_size(self.config.pen_width)
            self.toolbar.set_paper_style(self.config.paper_style)
            self.canvas.update()

    # -------------------------------------------------------------------------
    # Drag and Drop File Opening
    # -------------------------------------------------------------------------

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(('.touchwrite', '.json')):
                    event.acceptProposedAction()
                    return
        super().dragEnterEvent(event)

    def dropEvent(self, event) -> None:
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath.lower().endswith(('.touchwrite', '.json')):
                self._load_from_filepath(filepath)
                event.acceptProposedAction()
                break

    def _load_from_filepath(self, filepath: str) -> None:
        """Safely load and apply session file."""
        try:
            strokes, meta = self.session_manager.load_session(filepath)
            self.canvas.strokes = strokes
            self.canvas.history.clear()
            if "paper_style" in meta:
                try:
                    style = PaperStyle(meta["paper_style"])
                    self.canvas.set_paper_style(style)
                    self.toolbar.set_paper_style(style)
                except ValueError:
                    pass
            self.canvas.update()
            self.status_widget.set_stroke_count(len(strokes))
            self.statusBar().showMessage(f"Loaded: {filepath}", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Open Error", f"Failed to open notebook session:\n{e}")

    # -------------------------------------------------------------------------
    # Document Lifecycle (New, Open, Save, Export)
    # -------------------------------------------------------------------------

    def _on_action_new(self) -> None:
        if self.session_manager.is_dirty:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved handwriting. Would you like to save before creating a new notebook?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                self._on_action_save()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self.canvas.strokes.clear()
        self.canvas.history.clear()
        self.canvas.update()
        self.session_manager.reset_new()
        self.status_widget.set_stroke_count(0)

    def _on_action_open(self) -> None:
        if self.session_manager.is_dirty:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved handwriting. Save before opening another notebook?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                self._on_action_save()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open TouchWrite Session",
            "",
            "TouchWrite Notebooks (*.touchwrite *.json);;All Files (*.*)",
        )
        if filepath:
            self._load_from_filepath(filepath)

    def _on_action_save(self) -> None:
        if self.session_manager.current_filepath:
            self._save_to_file(self.session_manager.current_filepath)
        else:
            self._on_action_save_as()

    def _on_action_save_as(self) -> None:
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Notebook Session",
            os.path.join(os.path.expanduser("~"), "my_notes.touchwrite"),
            "TouchWrite Notebooks (*.touchwrite);;JSON Session (*.json)",
        )
        if filepath:
            self._save_to_file(filepath)

    def _save_to_file(self, filepath: str) -> None:
        if not filepath.lower().endswith(('.touchwrite', '.json')):
            filepath += ".touchwrite"
        try:
            self.session_manager.save_session(filepath, self.canvas.strokes)
            self.statusBar().showMessage(f"Saved: {filepath}", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save session:\n{e}")

    def _on_action_export(self) -> None:
        dlg = ExportDialog(default_filename=self.session_manager.get_document_name(), parent=self)
        if dlg.exec():
            filepath = dlg.selected_filepath
            fmt = dlg.selected_format
            try:
                if fmt == "png":
                    export_to_png(
                        filepath=filepath,
                        strokes=self.canvas.strokes,
                        config=self.config,
                        include_background=dlg.include_background,
                        transparent_bg=dlg.transparent_bg,
                        scale=dlg.scale,
                        crop_to_content=dlg.crop_to_content,
                    )
                elif fmt == "pdf":
                    export_to_pdf(
                        filepath=filepath,
                        strokes=self.canvas.strokes,
                        config=self.config,
                        include_background=dlg.include_background,
                    )
                elif fmt == "svg":
                    export_to_svg(
                        filepath=filepath,
                        strokes=self.canvas.strokes,
                        config=self.config,
                        include_background=dlg.include_background,
                    )
                self.statusBar().showMessage(f"Exported successfully: {filepath}", 5000)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export {fmt.upper()}:\n{e}")

    def _on_action_clear(self) -> None:
        if not self.canvas.strokes:
            return
        reply = QMessageBox.question(
            self,
            "Clear Canvas",
            "Are you sure you want to clear the entire page? (This action can be undone with Ctrl+Z)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.canvas.clear_canvas()

    def _show_guide(self) -> None:
        QMessageBox.information(
            self,
            "TouchWrite Touchpad Gestures & Handwriting Guide",
            "<h3>Touchpad Gestures & Tablet Mode:</h3>"
            "<ul>"
            "<li><b>👆 1 Finger (Normal Mouse):</b><br>"
            "Move one finger across the touchpad to navigate the mouse cursor freely. Use it to select tools, pick colors, click menus, and adjust sliders without drawing accidental ink.</li><br>"
            "<li><b>✌️ 2 Fingers (Tablet Handwriting Mode):</b><br>"
            "Place two fingers on the touchpad and glide together to write in smooth vector ink, just like on an iPad or tablet. Lifting your fingers commits the stroke cleanly.</li><br>"
            "<li><b>🖐 3 Fingers (Page Scrolling & Panning):</b><br>"
            "Glide three fingers across the touchpad to scroll and pan the notebook sheet smoothly in any direction.</li><br>"
            "<li><b>🖱 External Mouse:</b><br>"
            "Works 100% as an ordinary mouse. Left-click drag to draw with the mouse; use the scroll wheel to scroll the page vertically.</li>"
            "</ul>",
        )

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About TouchWrite",
            "<b>TouchWrite</b> — Finger-Based Digital Handwriting for Windows 11<br>"
            "Version 1.0.0<br><br>"
            "Designed for Windows Precision Touchpads (Lenovo LOQ & Windows 11).<br>"
            "Preserves natural handwriting curves with high-fidelity vector spline rendering.",
        )

    def closeEvent(self, event) -> None:
        if self.session_manager.is_dirty:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved handwriting. Would you like to save before closing?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                self._on_action_save()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
