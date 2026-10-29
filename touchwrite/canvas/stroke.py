"""
Stroke and point data models for TouchWrite.
"""

from dataclasses import dataclass, field
import time
import math
from typing import List, Dict, Any, Optional
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPainterPath, QColor


@dataclass
class StrokePoint:
    """A single coordinate sample within a handwritten stroke."""
    x: float
    y: float
    pressure: float = 1.0
    timestamp: float = field(default_factory=time.time)

    def to_qpoint(self) -> QPointF:
        """Convert to QPointF."""
        return QPointF(self.x, self.y)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize point to dictionary."""
        return {
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "p": round(self.pressure, 3),
            "t": round(self.timestamp, 4),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrokePoint":
        """Deserialize point from dictionary."""
        return cls(
            x=float(data["x"]),
            y=float(data["y"]),
            pressure=float(data.get("p", 1.0)),
            timestamp=float(data.get("t", 0.0)),
        )


class Stroke:
    """A continuous handwritten ink stroke comprised of sequential points."""

    def __init__(
        self,
        points: Optional[List[StrokePoint]] = None,
        color: str = "#1A1A1A",
        width: float = 3.0,
        tool: str = "pen",
        opacity: float = 1.0,
    ):
        self.points: List[StrokePoint] = points or []
        self.color: str = color
        self.width: float = max(0.5, float(width))
        self.tool: str = tool
        self.opacity: float = max(0.0, min(1.0, float(opacity)))

        # Cached bounding box and QPainterPath for rapid redraws
        self._cached_path: Optional[QPainterPath] = None
        self._cached_rect: Optional[QRectF] = None
        self._is_dirty: bool = True

    def add_point(self, point: StrokePoint) -> None:
        """Add a point to the stroke and mark caches as dirty."""
        # Avoid duplicate co-located points that create zero-length singularities
        if self.points:
            last = self.points[-1]
            dist_sq = (point.x - last.x) ** 2 + (point.y - last.y) ** 2
            if dist_sq < 0.25:  # Less than 0.5px away
                return
        self.points.append(point)
        self._is_dirty = True

    def get_points(self) -> List[StrokePoint]:
        """Return the list of points."""
        return self.points

    def invalidate_cache(self) -> None:
        """Mark path and bounding box cache as needing recalculation."""
        self._is_dirty = True
        self._cached_path = None
        self._cached_rect = None

    def get_bounding_rect(self) -> QRectF:
        """Calculate or return cached bounding rectangle including pen width."""
        if self._cached_rect is not None and not self._is_dirty:
            return self._cached_rect

        if not self.points:
            self._cached_rect = QRectF(0, 0, 0, 0)
            return self._cached_rect

        min_x = min(p.x for p in self.points)
        max_x = max(p.x for p in self.points)
        min_y = min(p.y for p in self.points)
        max_y = max(p.y for p in self.points)

        margin = self.width * 2.0
        self._cached_rect = QRectF(
            min_x - margin,
            min_y - margin,
            (max_x - min_x) + margin * 2,
            (max_y - min_y) + margin * 2,
        )
        return self._cached_rect

    def build_path(self) -> QPainterPath:
        """
        Build a smooth QPainterPath using midpoint quadratic Bézier splines.
        This produces natural, organic handwriting curves without rigid polyline corners.
        """
        if self._cached_path is not None and not self._is_dirty:
            return self._cached_path

        path = QPainterPath()
        pts = self.points
        n = len(pts)

        if n == 0:
            self._cached_path = path
            self._is_dirty = False
            return path

        if n == 1:
            # Single dot
            p = pts[0]
            r = self.width / 2.0
            path.addEllipse(QPointF(p.x, p.y), r, r)
            self._cached_path = path
            self._is_dirty = False
            return path

        if n == 2:
            path.moveTo(pts[0].to_qpoint())
            path.lineTo(pts[1].to_qpoint())
            self._cached_path = path
            self._is_dirty = False
            return path

        # For 3 or more points: Smooth midpoint quadratic Bézier curves
        path.moveTo(pts[0].to_qpoint())

        for i in range(1, n - 1):
            p_curr = pts[i]
            p_next = pts[i + 1]
            # Midpoint between current and next point
            mid_x = (p_curr.x + p_next.x) / 2.0
            mid_y = (p_curr.y + p_next.y) / 2.0
            path.quadTo(p_curr.to_qpoint(), QPointF(mid_x, mid_y))

        # Final segment connects to the last recorded point
        path.lineTo(pts[-1].to_qpoint())

        self._cached_path = path
        self._is_dirty = False
        return path

    def distance_to_point(self, pt: QPointF) -> float:
        """
        Calculate the minimum Euclidean distance from a test point to any segment of this stroke.
        Used for stroke-based eraser hit testing.
        """
        if not self.points:
            return float("inf")

        # Fast bounding box check first
        bbox = self.get_bounding_rect()
        if not bbox.contains(pt):
            # Compute distance to bbox
            dx = max(bbox.left() - pt.x(), 0, pt.x() - bbox.right())
            dy = max(bbox.top() - pt.y(), 0, pt.y() - bbox.bottom())
            if math.hypot(dx, dy) > 30.0:
                return float("inf")

        min_dist = float("inf")
        px, py = pt.x(), pt.y()

        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]

            # Segment distance formula
            vx = p2.x - p1.x
            vy = p2.y - p1.y
            seg_len_sq = vx * vx + vy * vy

            if seg_len_sq < 1e-6:
                d = math.hypot(px - p1.x, py - p1.y)
            else:
                # Projection parameter t
                t = max(0.0, min(1.0, ((px - p1.x) * vx + (py - p1.y) * vy) / seg_len_sq))
                proj_x = p1.x + t * vx
                proj_y = p1.y + t * vy
                d = math.hypot(px - proj_x, py - proj_y)

            if d < min_dist:
                min_dist = d

        return min_dist

    def to_dict(self) -> Dict[str, Any]:
        """Serialize stroke to dictionary format."""
        return {
            "points": [p.to_dict() for p in self.points],
            "color": self.color,
            "width": self.width,
            "tool": self.tool,
            "opacity": self.opacity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Stroke":
        """Deserialize stroke from dictionary format."""
        pts = [StrokePoint.from_dict(p) for p in data.get("points", [])]
        return cls(
            points=pts,
            color=data.get("color", "#1A1A1A"),
            width=float(data.get("width", 3.0)),
            tool=data.get("tool", "pen"),
            opacity=float(data.get("opacity", 1.0)),
        )
