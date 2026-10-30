"""
Custom interactive writing canvas widget for TouchWrite.
"""

from typing import List, Optional
import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QMouseEvent,
    QWheelEvent,
    QKeyEvent,
    QCursor,
    QTabletEvent,
)

from touchwrite.config import AppConfig, ToolMode, PaperStyle
from touchwrite.canvas.stroke import Stroke, StrokePoint
from touchwrite.canvas.renderer import InkRenderer
from touchwrite.canvas.paper import PaperRenderer
from touchwrite.canvas.history import (
    HistoryManager,
    AddStrokeAction,
    EraseStrokesAction,
    ClearCanvasAction,
)


class TouchCanvas(QWidget):
    """
    Main interactive canvas widget supporting smooth digital handwriting,
    touchpad inputs, stroke erasing, zooming, panning, and notebook paper backgrounds.
    """

    # Signals
    inking_changed = Signal(bool)             # True when currently drawing ink
    cursor_moved = Signal(float, float)        # Coordinates on canvas (x, y)
    stroke_count_changed = Signal(int)         # Total strokes currently on canvas
    history_changed = Signal(bool, bool)       # (can_undo, can_redo)
    zoom_changed = Signal(float)               # Current zoom level (e.g., 1.0 = 100%)

    def __init__(self, config: Optional[AppConfig] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config = config or AppConfig()

        # Canvas properties
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)

        # Drawing state
        self.strokes: List[Stroke] = []
        self.current_stroke: Optional[Stroke] = None
        self.active_tool: ToolMode = ToolMode.PEN
        self.is_inking: bool = False

        # Virtual Paper Dimensions (Portrait standard notebook page)
        self.paper_width: float = float(self.config.canvas_width)
        self.paper_height: float = float(self.config.canvas_height)

        # Zoom & Pan Transform
        self.zoom: float = 1.0
        self.pan_offset: QPointF = QPointF(40.0, 40.0)
        self._is_panning: bool = False
        self._last_pan_pos: QPointF = QPointF(0, 0)

        # Eraser visual cursor
        self._eraser_pos: Optional[QPointF] = None
        self._erased_in_current_drag: List[Stroke] = []
        self._erased_indices_in_drag: List[int] = []
        self._last_three_finger_pos: Optional[QPointF] = None

        # History manager
        self.history = HistoryManager()
        self.history.on_change = lambda u, r: self.history_changed.emit(u, r)

        # Input Manager reference
        self.input_manager = None

        self._update_cursor()

    def set_input_manager(self, input_manager) -> None:
        """Connect input manager for coordinated event routing."""
        self.input_manager = input_manager

    # -------------------------------------------------------------------------
    # Coordinate Transformations
    # -------------------------------------------------------------------------

    def screen_to_canvas(self, screen_pt: QPointF) -> QPointF:
        """Convert widget screen coordinates into virtual paper canvas coordinates."""
        cx = (screen_pt.x() - self.pan_offset.x()) / self.zoom
        cy = (screen_pt.y() - self.pan_offset.y()) / self.zoom
        return QPointF(cx, cy)

    def canvas_to_screen(self, canvas_pt: QPointF) -> QPointF:
        """Convert virtual paper canvas coordinates into widget screen coordinates."""
        sx = canvas_pt.x() * self.zoom + self.pan_offset.x()
        sy = canvas_pt.y() * self.zoom + self.pan_offset.y()
        return QPointF(sx, sy)

    def get_paper_rect(self) -> QRectF:
        """Get the bounding rectangle of the virtual paper sheet."""
        return QRectF(0, 0, self.paper_width, self.paper_height)

    def get_visible_canvas_rect(self) -> QRectF:
        """Get the rectangle of canvas currently visible within the viewport."""
        top_left = self.screen_to_canvas(QPointF(0, 0))
        bottom_right = self.screen_to_canvas(QPointF(self.width(), self.height()))
        return QRectF(top_left, bottom_right)

    # -------------------------------------------------------------------------
    # Stroke Lifecycle (Called by Input Adapters or Internal Events)
    # -------------------------------------------------------------------------

    def start_stroke(self, canvas_pt: QPointF, pressure: float = 1.0) -> None:
        """Begin a new stroke or eraser action at given canvas coordinates."""
        if self.active_tool == ToolMode.PEN:
            self.current_stroke = Stroke(
                color=self.config.pen_color,
                width=self.config.pen_width,
                tool="pen",
                opacity=self.config.pen_opacity,
            )
            pt = StrokePoint(canvas_pt.x(), canvas_pt.y(), pressure=pressure)
            self.current_stroke.add_point(pt)
            self.is_inking = True
            self.inking_changed.emit(True)
            self.update()

        elif self.active_tool == ToolMode.ERASER:
            self._erased_in_current_drag.clear()
            self._erased_indices_in_drag.clear()
            self._apply_eraser_at(canvas_pt)
            self.update()

    def continue_stroke(self, canvas_pt: QPointF, pressure: float = 1.0) -> None:
        """Extend current stroke or continue erasing."""
        if self.active_tool == ToolMode.PEN and self.current_stroke is not None:
            pt = StrokePoint(canvas_pt.x(), canvas_pt.y(), pressure=pressure)
            self.current_stroke.add_point(pt)
            self.update()

        elif self.active_tool == ToolMode.ERASER:
            self._apply_eraser_at(canvas_pt)
            self.update()

    def end_stroke(self) -> None:
        """Finish the active stroke and commit to undo history."""
        if self.active_tool == ToolMode.PEN and self.current_stroke is not None:
            if self.current_stroke.points:
                self.strokes.append(self.current_stroke)
                self.history.push_action(AddStrokeAction(self.current_stroke))
                self.stroke_count_changed.emit(len(self.strokes))
            self.current_stroke = None
            self.is_inking = False
            self.inking_changed.emit(False)
            self.update()

        elif self.active_tool == ToolMode.ERASER:
            if self._erased_in_current_drag:
                action = EraseStrokesAction(
                    self._erased_in_current_drag,
                    self._erased_indices_in_drag,
                )
                self.history.push_action(action)
                self.stroke_count_changed.emit(len(self.strokes))
                self._erased_in_current_drag.clear()
                self._erased_indices_in_drag.clear()
            self.is_inking = False
            self.inking_changed.emit(False)
            self.update()

    def cancel_stroke(self) -> None:
        """Cancel an in-progress stroke without saving it."""
        self.current_stroke = None
        self.is_inking = False
        self.inking_changed.emit(False)
        self.update()

    # -------------------------------------------------------------------------
    # Eraser Logic
    # -------------------------------------------------------------------------

    def _apply_eraser_at(self, canvas_pt: QPointF) -> None:
        """Erase strokes near the specified canvas point."""
        threshold = max(10.0, self.config.eraser_width)
        to_remove = []

        for idx, stroke in enumerate(self.strokes):
            if stroke in self._erased_in_current_drag:
                continue
            dist = stroke.distance_to_point(canvas_pt)
            if dist <= threshold:
                to_remove.append((idx, stroke))

        for idx, stroke in reversed(to_remove):
            self.strokes.remove(stroke)
            self._erased_in_current_drag.append(stroke)
            self._erased_indices_in_drag.append(idx)

    # -------------------------------------------------------------------------
    # Undo, Redo, Clear
    # -------------------------------------------------------------------------

    def undo(self) -> bool:
        """Undo last action."""
        if self.history.undo(self.strokes):
            self.stroke_count_changed.emit(len(self.strokes))
            self.update()
            return True
        return False

    def redo(self) -> bool:
        """Redo last undone action."""
        if self.history.redo(self.strokes):
            self.stroke_count_changed.emit(len(self.strokes))
            self.update()
            return True
        return False

    def clear_canvas(self) -> None:
        """Clear all strokes from canvas with full undo support."""
        if not self.strokes:
            return
        action = ClearCanvasAction(self.strokes)
        self.strokes.clear()
        self.current_stroke = None
        self.history.push_action(action)
        self.stroke_count_changed.emit(0)
        self.update()

    # -------------------------------------------------------------------------
    # Tool Selection & Configuration
    # -------------------------------------------------------------------------

    def set_tool(self, tool: ToolMode) -> None:
        """Set current active tool (PEN, ERASER, PAN)."""
        self.active_tool = tool
        self._update_cursor()
        self.update()

    def set_pen_width(self, width: float) -> None:
        """Set active pen stroke width."""
        self.config.pen_width = max(0.5, float(width))

    def set_pen_color(self, color_hex: str) -> None:
        """Set active pen stroke color."""
        self.config.pen_color = color_hex

    def set_paper_style(self, style: PaperStyle) -> None:
        """Change paper background style (blank, ruled, grid)."""
        self.config.paper_style = style
        self.update()

    def _update_cursor(self) -> None:
        """Update cursor shape based on active tool."""
        if self.active_tool == ToolMode.PEN:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif self.active_tool == ToolMode.ERASER:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        elif self.active_tool == ToolMode.PAN:
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    # -------------------------------------------------------------------------
    # Zoom and Pan Navigation
    # -------------------------------------------------------------------------

    def set_zoom(self, factor: float, anchor_screen: Optional[QPointF] = None) -> None:
        """Set zoom factor anchored to a screen point."""
        new_zoom = max(0.25, min(4.0, factor))
        if math.isclose(new_zoom, self.zoom):
            return

        if anchor_screen is None:
            anchor_screen = QPointF(self.width() / 2.0, self.height() / 2.0)

        # Keep the point under anchor_screen invariant
        canvas_before = self.screen_to_canvas(anchor_screen)
        self.zoom = new_zoom
        # Compute new offset
        self.pan_offset = QPointF(
            anchor_screen.x() - canvas_before.x() * self.zoom,
            anchor_screen.y() - canvas_before.y() * self.zoom,
        )
        self.zoom_changed.emit(self.zoom)
        self.update()

    def zoom_in(self) -> None:
        self.set_zoom(self.zoom * 1.25)

    def zoom_out(self) -> None:
        self.set_zoom(self.zoom * 0.8)

    def reset_view(self) -> None:
        """Reset view to 100% zoom and default margin offset."""
        self.zoom = 1.0
        self.pan_offset = QPointF(40.0, 40.0)
        self.zoom_changed.emit(self.zoom)
        self.update()

    def fit_page_width(self) -> None:
        """Fit virtual paper width to current window width."""
        available_w = max(100.0, float(self.width() - 80.0))
        fit_zoom = available_w / self.paper_width
        self.zoom = max(0.25, min(3.0, fit_zoom))
        self.pan_offset = QPointF(40.0, 40.0)
        self.zoom_changed.emit(self.zoom)
        self.update()

    # -------------------------------------------------------------------------
    # Painting
    # -------------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        """Draw the paper background, ruled lines, ink strokes, and tools."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 1. Fill canvas backdrop (neutral desktop area outside virtual paper)
        is_dark = self.config.theme == "dark"
        backdrop_col = QColor("#09090B") if is_dark else QColor("#E4E4E7")
        painter.fillRect(self.rect(), QBrush(backdrop_col))

        # 2. Apply Zoom and Pan transform
        painter.save()
        painter.translate(self.pan_offset)
        painter.scale(self.zoom, self.zoom)

        paper_rect = self.get_paper_rect()

        # Draw paper drop shadow
        shadow_rect = paper_rect.adjusted(4, 4, 8, 8)
        shadow_col = QColor(0, 0, 0, 40 if not is_dark else 100)
        painter.fillRect(shadow_rect, QBrush(shadow_col))

        # 3. Draw Paper Background (Blank / Ruled / Grid)
        PaperRenderer.render(
            painter=painter,
            rect=paper_rect,
            style=self.config.paper_style,
            spacing=self.config.paper_line_spacing,
            margin_x=self.config.paper_margin,
            dark_mode=is_dark,
        )

        # 4. Clip to virtual paper sheet
        painter.setClipRect(paper_rect)

        # 5. Render Completed Strokes
        visible_rect = self.get_visible_canvas_rect()
        InkRenderer.render_all(
            painter=painter,
            strokes=self.strokes,
            clip_rect=visible_rect,
            pressure_sim=self.config.pressure_simulation,
        )

        # 6. Render Active Stroke in Progress
        if self.current_stroke is not None and self.current_stroke.points:
            InkRenderer.render_stroke(
                painter=painter,
                stroke=self.current_stroke,
                pressure_sim=self.config.pressure_simulation,
            )

        painter.restore()

        # 7. Draw Eraser Ring Cursor in Screen Space
        if self.active_tool == ToolMode.ERASER and self._eraser_pos is not None:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            eraser_r = (self.config.eraser_width * self.zoom) / 2.0
            pen = QPen(QColor(239, 68, 68, 200), 1.5, Qt.PenStyle.DashLine)
            brush = QBrush(QColor(239, 68, 68, 30))
            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawEllipse(self._eraser_pos, eraser_r, eraser_r)
            painter.restore()

    # -------------------------------------------------------------------------
    # Mouse & Pointer Event Handling (Direct or Fallback)
    # -------------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press."""
        pos = event.position()
        self.cursor_moved.emit(pos.x(), pos.y())

        # Middle button or Pan tool -> Start panning
        if event.button() == Qt.MouseButton.MiddleButton or self.active_tool == ToolMode.PAN:
            self._is_panning = True
            self._last_pan_pos = pos
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        # Eraser Tool -> Begin erase drag
        if self.active_tool == ToolMode.ERASER:
            if event.button() == Qt.MouseButton.LeftButton:
                canvas_pt = self.screen_to_canvas(pos)
                self.start_stroke(canvas_pt, pressure=1.0)
            return

        # Pen Tool -> Delegate to active input adapter
        if self.active_tool == ToolMode.PEN and self.input_manager:
            if self.input_manager.dispatch_mouse_press(event):
                return

        # Fallback if unhandled
        if event.button() == Qt.MouseButton.LeftButton:
            canvas_pt = self.screen_to_canvas(pos)
            if self.get_paper_rect().contains(canvas_pt):
                self.start_stroke(canvas_pt, pressure=1.0)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse movement / dragging."""
        pos = event.position()
        canvas_pt = self.screen_to_canvas(pos)
        self.cursor_moved.emit(canvas_pt.x(), canvas_pt.y())

        if self.active_tool == ToolMode.ERASER:
            self._eraser_pos = pos

        # If panning
        if self._is_panning:
            delta = pos - self._last_pan_pos
            self.pan_offset += delta
            self._last_pan_pos = pos
            self.update()
            return

        # If Eraser Tool
        if self.active_tool == ToolMode.ERASER:
            is_erasing = bool(event.buttons() & Qt.MouseButton.LeftButton)
            if self.input_manager:
                if self.config.tablet_touchpad_mode and not self.input_manager.is_external_mouse_active():
                    is_erasing = True
                elif hasattr(self.input_manager, 'touchpad_adapter') and self.input_manager.touchpad_adapter.is_trigger_held:
                    is_erasing = True
            if is_erasing:
                self.continue_stroke(canvas_pt, pressure=1.0)
            self.update()
            return

        # Pen Tool -> Delegate to active input adapter
        if self.active_tool == ToolMode.PEN and self.input_manager:
            if self.input_manager.dispatch_mouse_move(event):
                return
            # If not handled by adapter (e.g. mouse cursor hover or finger lifted), do not draw!
            return

        # Fallback only if no input manager and mouse left button is held
        if self.is_inking and (event.buttons() & Qt.MouseButton.LeftButton):
            self.continue_stroke(canvas_pt, pressure=1.0)

    def pan_by_mouse_move(self, event: QMouseEvent) -> None:
        """Pan the canvas when 3 fingers are dragged across the touchpad."""
        pos = event.position()
        if self._last_three_finger_pos is not None:
            delta = pos - self._last_three_finger_pos
            self.pan_offset += delta
            self.update()
        self._last_three_finger_pos = pos

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release."""
        self._last_three_finger_pos = None
        if event.button() == Qt.MouseButton.MiddleButton or (self._is_panning and self.active_tool == ToolMode.PAN):
            self._is_panning = False
            self._update_cursor()
            return

        if self.active_tool == ToolMode.ERASER:
            if event.button() == Qt.MouseButton.LeftButton:
                self.end_stroke()
            return

        if self.active_tool == ToolMode.PEN and self.input_manager:
            if self.input_manager.dispatch_mouse_release(event):
                return

        if event.button() == Qt.MouseButton.LeftButton and self.is_inking:
            self.end_stroke()

    def tabletEvent(self, event: QTabletEvent) -> None:
        """Handle tablet / stylus pen events with true hardware pressure."""
        if self.input_manager:
            if self.input_manager.dispatch_tablet_event(event):
                return
        super().tabletEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Route keyboard events to input manager for Hold-to-Write mode."""
        if self.input_manager:
            if self.input_manager.dispatch_key_press(event):
                event.accept()
                return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """Route keyboard release events to input manager."""
        if self.input_manager:
            if self.input_manager.dispatch_key_release(event):
                event.accept()
                return
        super().keyReleaseEvent(event)

    def focusOutEvent(self, event) -> None:
        """Reset trigger key state if canvas loses focus."""
        if self.input_manager and hasattr(self.input_manager, 'touchpad_adapter'):
            tp = self.input_manager.touchpad_adapter
            if tp.is_trigger_held:
                tp.is_trigger_held = False
                if tp.is_writing:
                    self.end_stroke()
                    tp.is_writing = False
        super().focusOutEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Handle mouse wheel and touchpad gestures:
        - 2 Fingers on Touchpad: Writes ink (Tablet Mode)
        - 3 Fingers on Touchpad: Scrolls / pans the page
        - Physical Mouse Wheel: Scrolls the page vertically
        - Ctrl + Wheel: Zooms the page
        """
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom with Ctrl + Wheel
            delta = event.angleDelta().y()
            factor = 1.15 if delta > 0 else 0.85
            self.set_zoom(self.zoom * factor, anchor_screen=event.position())
            event.accept()
            return

        is_touchpad_gesture = (event.source() == Qt.MouseEventSource.MouseEventSynthesizedBySystem) or (not event.pixelDelta().isNull())
        is_three_finger = False
        if self.input_manager and hasattr(self.input_manager, 'win_pointer_adapter'):
            is_three_finger = (self.input_manager.win_pointer_adapter.contact_count >= 3) or self.input_manager.win_pointer_adapter.is_three_finger_scrolling

        # If 3 fingers on touchpad, or physical mouse wheel, or in Pan tool, or tablet mode OFF: SCROLL / PAN THE PAGE!
        if is_three_finger or not is_touchpad_gesture or self.active_tool == ToolMode.PAN or not self.config.tablet_touchpad_mode:
            dx = event.pixelDelta().x() if not event.pixelDelta().isNull() else event.angleDelta().x() / 2.0
            dy = event.pixelDelta().y() if not event.pixelDelta().isNull() else event.angleDelta().y() / 2.0
            self.pan_offset += QPointF(dx, dy)
            self.update()
            event.accept()
            return

        # Otherwise: 2 Fingers on Touchpad -> TABLET INKING MODE!
        if self.active_tool == ToolMode.PEN:
            pos = event.position()
            canvas_pt = self.screen_to_canvas(pos)
            if self.get_paper_rect().contains(canvas_pt):
                phase = event.phase()
                if phase == Qt.ScrollPhase.ScrollBegin or not self.is_inking:
                    self.start_stroke(canvas_pt, pressure=1.0)
                else:
                    self.continue_stroke(canvas_pt, pressure=1.0)

                # Restart dwell timer so lifting fingers commits the stroke in 50ms
                if self.input_manager and hasattr(self.input_manager, 'touchpad_adapter'):
                    self.input_manager.touchpad_adapter.dwell_timer.start(50)

                if phase == Qt.ScrollPhase.ScrollEnd:
                    self.end_stroke()

                event.accept()
                return

        event.accept()

    def leaveEvent(self, event) -> None:
        """Hide eraser cursor and commit stroke if leaving paper."""
        self._eraser_pos = None
        if self.config.input_mode == InputMode.DIRECT_CONTACT and self.is_inking:
            self.end_stroke()
        self.update()
        super().leaveEvent(event)
