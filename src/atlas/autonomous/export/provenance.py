
"""Provenance export."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.autonomous.export.json_export import write_json
from atlas.autonomous.export.markdown import write_markdown


def build_provenance_markdown(provenance: dict[str, Any]) -> str:
    """Build provenance markdown."""
    lines = [
        "# Atlas Provenance Report",
        "",
        provenance.get("summary", "No provenance summary available."),
        "",
    ]

    graph_summary = ((provenance.get("graph", {}) or {}).get("summary", {}) or {})

    lines.extend([
        "## Graph Summary",
        "",
        f"- Node count: `{graph_summary.get('node_count', 0)}`",
        f"- Edge count: `{graph_summary.get('edge_count', 0)}`",
        "",
        "## Object Types",
        "",
    ])

    for object_type, count in (graph_summary.get("object_types", {}) or {}).items():
        lines.append(f"- `{object_type}`: `{count}`")

    lines.extend(["", "## Lineage Relations", ""])

    relations = ((provenance.get("lineage", {}) or {}).get("relations", []) or [])
    for relation in relations:
        lines.append(
            f"- `{relation.get('parent')}` --{relation.get('relation')}--> `{relation.get('child')}`"
        )

    return "\n".join(lines)


def export_provenance(report: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    """Export provenance report."""
    target = Path(output_dir)
    provenance = report.get("provenance", {}) or {}
    return {
        "provenance_json": write_json(target / "provenance_report.json", provenance),
        "provenance": write_markdown(target / "provenance_report.md", build_provenance_markdown(provenance)),
    }
