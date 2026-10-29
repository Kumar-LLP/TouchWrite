"""
Canvas package for TouchWrite handwriting application.
"""

from touchwrite.canvas.stroke import Stroke, StrokePoint
from touchwrite.canvas.renderer import InkRenderer
from touchwrite.canvas.paper import PaperRenderer
from touchwrite.canvas.history import HistoryManager, Action
from touchwrite.canvas.canvas import TouchCanvas

__all__ = [
    "Stroke",
    "StrokePoint",
    "InkRenderer",
    "PaperRenderer",
    "HistoryManager",
    "Action",
    "TouchCanvas",
]
