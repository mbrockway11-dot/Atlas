"""Unified-canvas SVG rendering for all normalized Kamea streams."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from atlas.visualization.kamea_riverbed import PLANET_COLORS


CIPHER_DASH = {
    "ordinal": "",
    "hebrew_literal": "10 6",
    "hebrew_phonetic": "3 6",
}


def render_unified_kamea_shape_svg(shape: dict[str, Any], *, title: str = "Unified Kamea Shape", output_size: int = 900) -> str:
    padding = 90
    usable = output_size - padding * 2
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{output_size}" height="{output_size}" viewBox="0 0 {output_size} {output_size}">',
        f'<rect width="{output_size}" height="{output_size}" fill="#020617"/>',
        f'<text x="{output_size / 2}" y="42" fill="#f8fafc" font-size="28" font-weight="700" text-anchor="middle">{escape(title)}</text>',
        f'<text x="{output_size / 2}" y="68" fill="#94a3b8" font-size="14" text-anchor="middle">all 3×3 through 9×9 Kameas normalized to one unit field</text>',
        f'<rect x="{padding}" y="{padding}" width="{usable}" height="{usable}" fill="none" stroke="#475569" stroke-width="1.5"/>',
    ]
    for fraction in (0.25, 0.5, 0.75):
        point = padding + usable * fraction
        parts.append(f'<line x1="{padding}" y1="{point:.2f}" x2="{padding + usable}" y2="{point:.2f}" stroke="#334155" stroke-opacity="0.25"/>')
        parts.append(f'<line x1="{point:.2f}" y1="{padding}" x2="{point:.2f}" y2="{padding + usable}" stroke="#334155" stroke-opacity="0.25"/>')
    for stream in shape.get("streams", []) or []:
        points = stream.get("normalized_points", []) or []
        if len(points) < 2:
            continue
        planet = str(stream.get("planet") or "unknown")
        cipher = str(stream.get("cipher") or "unknown")
        color = PLANET_COLORS.get(planet, "#e2e8f0")
        dash = CIPHER_DASH.get(cipher, "2 5")
        point_string = " ".join(f"{padding + float(x) * usable:.2f},{padding + float(y) * usable:.2f}" for x, y in points)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(f'<polyline points="{point_string}" fill="none" stroke="{color}" stroke-width="2.4" stroke-opacity="0.32" stroke-linecap="round" stroke-linejoin="round"{dash_attr}/>')
        start_x, start_y = points[0]
        end_x, end_y = points[-1]
        parts.append(f'<circle cx="{padding + start_x * usable:.2f}" cy="{padding + start_y * usable:.2f}" r="4" fill="none" stroke="{color}" stroke-opacity="0.7"/>')
        parts.append(f'<line x1="{padding + end_x * usable - 5:.2f}" y1="{padding + end_y * usable:.2f}" x2="{padding + end_x * usable + 5:.2f}" y2="{padding + end_y * usable:.2f}" stroke="{color}" stroke-width="2" stroke-opacity="0.7"/>')
    legend_y = output_size - 35
    for index, planet in enumerate(("saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon")):
        x = 55 + index * 115
        color = PLANET_COLORS[planet]
        parts.append(f'<circle cx="{x}" cy="{legend_y}" r="6" fill="{color}"/>')
        parts.append(f'<text x="{x + 11}" y="{legend_y + 5}" fill="#cbd5e1" font-size="13">{planet.title()}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def export_unified_kamea_shape_svg(shape: dict[str, Any], output_path: str | Path, *, title: str = "Unified Kamea Shape", output_size: int = 900) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_unified_kamea_shape_svg(shape, title=title, output_size=output_size), encoding="utf-8")
    return path
