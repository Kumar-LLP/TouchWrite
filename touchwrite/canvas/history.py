"""
Undo and redo action history stack for TouchWrite canvas operations.
"""

from typing import List, Callable, Optional
from touchwrite.canvas.stroke import Stroke


class Action:
    """Base class for undoable canvas actions."""

    def undo(self, strokes: List[Stroke]) -> None:
        raise NotImplementedError

    def redo(self, strokes: List[Stroke]) -> None:
        raise NotImplementedError


class AddStrokeAction(Action):
    """Action representing the addition of a new handwritten stroke."""

    def __init__(self, stroke: Stroke):
        self.stroke = stroke

    def undo(self, strokes: List[Stroke]) -> None:
        if self.stroke in strokes:
            strokes.remove(self.stroke)

    def redo(self, strokes: List[Stroke]) -> None:
        strokes.append(self.stroke)


class EraseStrokesAction(Action):
    """Action representing the erasure of one or more strokes."""

    def __init__(self, erased_strokes: List[Stroke], indices: List[int]):
        self.erased_strokes = list(erased_strokes)
        self.indices = list(indices)

    def undo(self, strokes: List[Stroke]) -> None:
        # Re-insert strokes at original indices if possible
        for idx, stroke in zip(self.indices, self.erased_strokes):
            if idx <= len(strokes):
                strokes.insert(idx, stroke)
            else:
                strokes.append(stroke)

    def redo(self, strokes: List[Stroke]) -> None:
        for stroke in self.erased_strokes:
            if stroke in strokes:
                strokes.remove(stroke)


class ClearCanvasAction(Action):
    """Action representing clearing all strokes from the canvas."""

    def __init__(self, previous_strokes: List[Stroke]):
        self.previous_strokes = list(previous_strokes)

    def undo(self, strokes: List[Stroke]) -> None:
        strokes.clear()
        strokes.extend(self.previous_strokes)

    def redo(self, strokes: List[Stroke]) -> None:
        strokes.clear()


class HistoryManager:
    """Manages undo and redo stacks for drawing operations."""

    def __init__(self, max_history: int = 150):
        self.max_history = max_history
        self._undo_stack: List[Action] = []
        self._redo_stack: List[Action] = []
        self.on_change: Optional[Callable[[bool, bool], None]] = None

    def _notify(self) -> None:
        if self.on_change:
            self.on_change(self.can_undo, self.can_redo)

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def push_action(self, action: Action) -> None:
        """Push a newly executed action onto the undo stack."""
        self._undo_stack.append(action)
        if len(self._undo_stack) > self.max_history:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self._notify()

    def undo(self, strokes: List[Stroke]) -> bool:
        """Undo the most recent action."""
        if not self._undo_stack:
            return False
        action = self._undo_stack.pop()
        action.undo(strokes)
        self._redo_stack.append(action)
        self._notify()
        return True

    def redo(self, strokes: List[Stroke]) -> bool:
        """Redo the most recent undone action."""
        if not self._redo_stack:
            return False
        action = self._redo_stack.pop()
        action.redo(strokes)
        self._undo_stack.append(action)
        self._notify()
        return True

    def clear(self) -> None:
        """Clear both undo and redo stacks."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._notify()
