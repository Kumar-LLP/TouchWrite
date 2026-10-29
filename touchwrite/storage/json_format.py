"""
Lossless JSON vector session storage format for TouchWrite notebooks.
"""

import json
import os
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Tuple
from touchwrite.canvas.stroke import Stroke
from touchwrite.config import AppConfig, PaperStyle


FORMAT_VERSION = "1.0"
APP_SIGNATURE = "TouchWrite"


def serialize_session(strokes: List[Stroke], config: AppConfig) -> Dict[str, Any]:
    """Serialize the drawing session into a structured vector dictionary."""
    return {
        "app": APP_SIGNATURE,
        "version": FORMAT_VERSION,
        "saved_at": datetime.now().isoformat(),
        "canvas": {
            "width": config.canvas_width,
            "height": config.canvas_height,
            "paper_style": config.paper_style.value,
            "paper_line_spacing": config.paper_line_spacing,
            "paper_margin": config.paper_margin,
        },
        "stroke_count": len(strokes),
        "strokes": [stroke.to_dict() for stroke in strokes],
    }


def deserialize_session(data: Dict[str, Any]) -> Tuple[List[Stroke], Dict[str, Any]]:
    """
    Deserialize vector dictionary into strokes and canvas metadata.
    Validates structure and provides friendly error messages on corrupt data.
    """
    if not isinstance(data, dict):
        raise ValueError("Invalid session file: root must be a JSON object.")

    app = data.get("app")
    if app != APP_SIGNATURE:
        raise ValueError(f"Unrecognized file format: expected app '{APP_SIGNATURE}', found '{app}'.")

    raw_strokes = data.get("strokes", [])
    if not isinstance(raw_strokes, list):
        raise ValueError("Corrupt file: 'strokes' property must be a list.")

    strokes: List[Stroke] = []
    for idx, s_data in enumerate(raw_strokes):
        try:
            strokes.append(Stroke.from_dict(s_data))
        except Exception as e:
            # Continue loading surviving strokes if one is damaged
            print(f"Warning: Skipping corrupted stroke index {idx}: {e}")

    canvas_meta = data.get("canvas", {})
    return strokes, canvas_meta


def save_session_file(filepath: str, strokes: List[Stroke], config: AppConfig) -> None:
    """
    Atomically save session data to disk using a temporary file.
    Prevents corrupt files if the write is interrupted.
    """
    data = serialize_session(strokes, config)
    directory = os.path.dirname(os.path.abspath(filepath))
    os.makedirs(directory, exist_ok=True)

    # Atomic write pattern
    with tempfile.NamedTemporaryFile("w", dir=directory, delete=False, encoding="utf-8") as tf:
        json.dump(data, tf, indent=2, ensure_ascii=False)
        temp_name = tf.name

    if os.path.exists(filepath):
        os.replace(temp_name, filepath)
    else:
        os.rename(temp_name, filepath)


def load_session_file(filepath: str) -> Tuple[List[Stroke], Dict[str, Any]]:
    """Load and validate session from disk."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Session file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return deserialize_session(data)
