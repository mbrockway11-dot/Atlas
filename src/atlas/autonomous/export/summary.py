
"""Autonomous summary export."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.autonomous.export.json_export import write_json
from atlas.autonomous.export.markdown import metric_lines, write_markdown


def build_summary_markdown(report: dict[str, Any]) -> str:
    """Build autonomous summary markdown."""
    learning = report.get("learning_update", {}) or {}
    confidence = report.get("scientific_confidence", {}) or {}
    theory = report.get("theory", {}) or {}
    prediction = report.get("prediction", {}) or {}

    lines = [
        "# Atlas Autonomous Summary",
        "",
        report.get("summary", "No summary available."),
        "",
        "## Key Metrics",
        "",
        *metric_lines({
            "Learning label": learning.get("learning_label", "n/a"),
            "Learning score": learning.get("learning_score", "n/a"),
            "Scientific confidence": confidence.get("scientific_confidence", "n/a"),
            "Confidence label": confidence.get("confidence_label", "n/a"),
            "Promoted theories": theory.get("promoted_count", 0),
            "Prediction summary": prediction.get("summary", "n/a"),
        }),
        "",
    ]

    return "\n".join(lines)


def export_summary(report: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    """Export autonomous summary."""
    target = Path(output_dir)
    return {
        "summary": write_markdown(target / "autonomous_summary.md", build_summary_markdown(report)),
        "json": write_json(target / "autonomous_report.json", report),
    }
