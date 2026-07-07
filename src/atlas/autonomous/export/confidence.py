
"""Scientific confidence export."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.autonomous.export.json_export import write_json
from atlas.autonomous.export.markdown import metric_lines, write_markdown


def build_confidence_markdown(confidence: dict[str, Any]) -> str:
    """Build scientific confidence markdown."""
    lines = [
        "# Atlas Scientific Confidence Report",
        "",
        confidence.get("summary", "No confidence summary available."),
        "",
        "## Confidence",
        "",
        *metric_lines({
            "Scientific confidence": confidence.get("scientific_confidence", "n/a"),
            "Confidence label": confidence.get("confidence_label", "n/a"),
        }),
        "",
        "## Components",
        "",
    ]

    for key, value in (confidence.get("components", {}) or {}).items():
        lines.append(f"- {key}: `{value}`")

    lines.extend(["", "## Inputs", ""])

    for key, value in (confidence.get("inputs", {}) or {}).items():
        lines.append(f"- {key}: `{value}`")

    return "\n".join(lines)


def export_confidence(report: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    """Export confidence report."""
    target = Path(output_dir)
    confidence = report.get("scientific_confidence", {}) or {}
    return {
        "confidence_json": write_json(target / "confidence_report.json", confidence),
        "confidence": write_markdown(target / "confidence_report.md", build_confidence_markdown(confidence)),
    }
