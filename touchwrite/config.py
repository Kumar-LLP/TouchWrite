"""
Configuration and default settings for TouchWrite.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any


class InputMode(str, Enum):
    """Writing input modes for laptop touchpads and pointers."""
    TABLET_TOUCHPAD = "tablet_touchpad"  # Dedicated single-finger tablet writing (Natural like an iPad/tablet)
    HOLD_TO_WRITE = "hold_to_write"      # Hold trigger key (e.g., Spacebar) while gliding finger
    DIRECT_CONTACT = "direct_contact"    # Move finger inside canvas area to write directly
    AUTO_DWELL = "auto_dwell"            # Automatic pen-up on pause/slow speed
    CLICK_AND_DRAG = "click_and_drag"    # Physical click or tap-and-slide
    PEN_TABLET = "pen_tablet"            # Windows Ink stylus or external tablet


class PaperStyle(str, Enum):
    """Paper background styles."""
    BLANK = "blank"
    RULED = "ruled"
    GRID = "grid"


class ToolMode(str, Enum):
    """Active canvas tool."""
    PEN = "pen"
    ERASER = "eraser"
    PAN = "pan"


@dataclass
class AppConfig:
    """TouchWrite application configuration settings."""
    # Tool defaults
    pen_width: float = 3.0
    pen_color: str = "#1A1A1A"  # Natural ink black
    pen_opacity: float = 1.0
    pressure_simulation: bool = True  # Modulate width with velocity
    min_width_factor: float = 0.6
    max_width_factor: float = 1.4

    # Eraser defaults
    eraser_width: float = 24.0
    stroke_eraser: bool = True  # Erase entire stroke on touch (notebook style)

    # Canvas defaults
    paper_style: PaperStyle = PaperStyle.RULED
    paper_line_spacing: int = 34  # Standard lined paper spacing in pixels
    paper_margin: int = 70        # Left margin line position
    canvas_width: int = 2400      # High-resolution virtual page width
    canvas_height: int = 3200     # High-resolution virtual page height

    # Input defaults
    input_mode: InputMode = InputMode.TABLET_TOUCHPAD
    tablet_touchpad_mode: bool = True  # Dedicated single-finger tablet mode
    finger_lift_timeout_ms: int = 50   # Snappy 50ms finger lift detection
    trigger_key: str = "Space"         # Spacebar trigger for secondary hold mode
    dwell_timeout_ms: int = 180        # Dwell timeout for slow auto-lift mode
    smoothing_factor: float = 0.6      # Catmull-Rom / Bézier smoothing aggressiveness

    # UI defaults
    theme: str = "light"          # "light" or "dark"
    show_coordinates: bool = True
    show_status_badge: bool = True

    # Color palette
    color_palette: list = field(default_factory=lambda: [
        "#111827",  # Deep Ink Black
        "#1E40AF",  # Classic Navy Blue
        "#991B1B",  # Editorial Crimson Red
        "#065F46",  # Forest Green
        "#7C3AED",  # Violet Purple
        "#D97706",  # Warm Amber
        "#4B5563",  # Pencil Graphite Grey
    ])

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "pen_width": self.pen_width,
            "pen_color": self.pen_color,
            "pen_opacity": self.pen_opacity,
            "pressure_simulation": self.pressure_simulation,
            "min_width_factor": self.min_width_factor,
            "max_width_factor": self.max_width_factor,
            "eraser_width": self.eraser_width,
            "stroke_eraser": self.stroke_eraser,
            "paper_style": self.paper_style.value,
            "paper_line_spacing": self.paper_line_spacing,
            "paper_margin": self.paper_margin,
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "input_mode": self.input_mode.value,
            "tablet_touchpad_mode": self.tablet_touchpad_mode,
            "finger_lift_timeout_ms": self.finger_lift_timeout_ms,
            "trigger_key": self.trigger_key,
            "dwell_timeout_ms": self.dwell_timeout_ms,
            "smoothing_factor": self.smoothing_factor,
            "theme": self.theme,
            "show_coordinates": self.show_coordinates,
            "show_status_badge": self.show_status_badge,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        """Instantiate config from dictionary with safety defaults."""
        config = cls()
        if not data:
            return config
        for key, value in data.items():
            if hasattr(config, key):
                if key == "paper_style":
                    try:
                        setattr(config, key, PaperStyle(value))
                    except ValueError:
                        pass
                elif key == "input_mode":
                    try:
                        setattr(config, key, InputMode(value))
                    except ValueError:
                        pass
                else:
                    setattr(config, key, value)
        return config
