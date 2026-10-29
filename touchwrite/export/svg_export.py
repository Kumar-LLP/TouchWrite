"""
Scalable Vector Graphics (SVG) exporter preserving exact Bézier stroke geometry.
"""

from typing import List
from touchwrite.canvas.stroke import Stroke
from touchwrite.config import AppConfig, PaperStyle


def export_to_svg(
    filepath: str,
    strokes: List[Stroke],
    config: AppConfig,
    include_background: bool = True,
) -> bool:
    """
    Export handwritten strokes to standard W3C SVG XML format.
    Preserves quadratic Bézier curves and antialiased round styling.
    """
    width = config.canvas_width
    height = config.canvas_height

    svg_lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '  <defs>',
        '    <style>',
        '      .ink-stroke { fill: none; stroke-linecap: round; stroke-linejoin: round; }',
        '      .paper-line { stroke: #D4D4D8; stroke-width: 1; }',
        '      .margin-line { stroke: #FCA5A5; stroke-width: 1.5; }',
        '    </style>',
        '  </defs>',
    ]

    # Background sheet
    if include_background:
        svg_lines.append(f'  <rect width="{width}" height="{height}" fill="#FAFAF9"/>')

        # Ruled lines
        if config.paper_style == PaperStyle.RULED:
            spacing = config.paper_line_spacing
            for y in range(spacing, height, spacing):
                svg_lines.append(f'  <line x1="0" y1="{y}" x2="{width}" y2="{y}" class="paper-line"/>')
            if config.paper_margin > 0:
                svg_lines.append(f'  <line x1="{config.paper_margin}" y1="0" x2="{config.paper_margin}" y2="{height}" class="margin-line"/>')

        # Grid lines
        elif config.paper_style == PaperStyle.GRID:
            spacing = max(16, config.paper_line_spacing)
            for y in range(spacing, height, spacing):
                svg_lines.append(f'  <line x1="0" y1="{y}" x2="{width}" y2="{y}" class="paper-line"/>')
            for x in range(spacing, width, spacing):
                svg_lines.append(f'  <line x1="{x}" y1="0" x2="{x}" y2="{height}" class="paper-line"/>')

    # Strokes group
    svg_lines.append('  <g id="TouchWriteStrokes">')

    for stroke in strokes:
        pts = stroke.points
        n = len(pts)
        if n == 0:
            continue

        color = stroke.color
        stroke_w = stroke.width
        opacity = stroke.opacity

        if n == 1:
            p = pts[0]
            r = stroke_w / 2.0
            svg_lines.append(
                f'    <circle cx="{p.x:.2f}" cy="{p.y:.2f}" r="{r:.2f}" fill="{color}" opacity="{opacity:.2f}"/>'
            )
            continue

        if n == 2:
            d_path = f"M {pts[0].x:.2f} {pts[0].y:.2f} L {pts[1].x:.2f} {pts[1].y:.2f}"
        else:
            # Quadratic Bézier path
            d_parts = [f"M {pts[0].x:.2f} {pts[0].y:.2f}"]
            for i in range(1, n - 1):
                p_curr = pts[i]
                p_next = pts[i + 1]
                mid_x = (p_curr.x + p_next.x) / 2.0
                mid_y = (p_curr.y + p_next.y) / 2.0
                d_parts.append(f"Q {p_curr.x:.2f} {p_curr.y:.2f} {mid_x:.2f} {mid_y:.2f}")
            d_parts.append(f"L {pts[-1].x:.2f} {pts[-1].y:.2f}")
            d_path = " ".join(d_parts)

        svg_lines.append(
            f'    <path d="{d_path}" class="ink-stroke" stroke="{color}" stroke-width="{stroke_w:.2f}" opacity="{opacity:.2f}"/>'
        )

    svg_lines.append('  </g>')
    svg_lines.append('</svg>')

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))

    return True
