"""
Session manager for document lifecycle, recent files, and change tracking.
"""

import os
from typing import Optional, List, Dict, Any, Tuple
from PySide6.QtCore import QObject, Signal

from touchwrite.canvas.stroke import Stroke
from touchwrite.config import AppConfig, PaperStyle
from touchwrite.storage.json_format import save_session_file, load_session_file


class SessionManager(QObject):
    """
    Manages active document filepath, modified status, save/load operations, and recent files.
    """

    dirty_changed = Signal(bool)           # True when unsaved changes exist
    title_changed = Signal(str)            # Document window title update
    file_saved = Signal(str)               # Emitted on successful save
    file_loaded = Signal(str)              # Emitted on successful open

    def __init__(self, config: Optional[AppConfig] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.config = config or AppConfig()
        self.current_filepath: Optional[str] = None
        self._is_dirty: bool = False

    @property
    def is_dirty(self) -> bool:
        return self._is_dirty

    def set_dirty(self, dirty: bool = True) -> None:
        if self._is_dirty != dirty:
            self._is_dirty = dirty
            self.dirty_changed.emit(dirty)
            self._update_title()

    def get_document_name(self) -> str:
        if self.current_filepath:
            return os.path.basename(self.current_filepath)
        return "Untitled Notebook"

    def _update_title(self) -> None:
        name = self.get_document_name()
        if self._is_dirty:
            name += " *"
        self.title_changed.emit(f"{name} - TouchWrite")

    def save_session(self, filepath: str, strokes: List[Stroke]) -> None:
        """Save session to specified filepath."""
        save_session_file(filepath, strokes, self.config)
        self.current_filepath = filepath
        self.set_dirty(False)
        self._update_title()
        self.file_saved.emit(filepath)

    def load_session(self, filepath: str) -> Tuple[List[Stroke], Dict[str, Any]]:
        """Load session from filepath."""
        strokes, meta = load_session_file(filepath)
        self.current_filepath = filepath
        self.set_dirty(False)
        self._update_title()
        self.file_loaded.emit(filepath)
        return strokes, meta

    def reset_new(self) -> None:
        """Reset session to new untitled state."""
        self.current_filepath = None
        self.set_dirty(False)
        self._update_title()
