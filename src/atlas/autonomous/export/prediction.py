
"""Prediction export."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.autonomous.export.markdown import write_markdown


def build_prediction_markdown(prediction: dict[str, Any]) -> str:
    """Build prediction benchmark markdown."""
    lines = [
        "# Atlas Prediction Benchmark",
        "",
        prediction.get("summary", "No prediction summary available."),
        "",
    ]

    if not prediction.get("success"):
        return "\n".join(lines)

    benchmark = prediction.get("benchmark", {}) or {}
    scores = benchmark.get("scores", {}) or {}
    split = benchmark.get("split", {}) or {}

    lines.extend([
        "## Split",
        "",
        f"- Train count: `{split.get('train_count', 0)}`",
        f"- Holdout count: `{split.get('holdout_count', 0)}`",
        "",
        "## Scores",
        "",
        f"- Mean absolute error: `{scores.get('mean_absolute_error')}`",
        f"- Max absolute error: `{scores.get('max_absolute_error')}`",
        f"- Accuracy label: `{scores.get('accuracy_label')}`",
        "",
        "## Target Scores",
        "",
    ])

    for target, values in (scores.get("targets", {}) or {}).items():
        lines.extend([
            f"### {target}",
            "",
            f"- Count: `{values.get('count')}`",
            f"- Mean absolute error: `{values.get('mean_absolute_error')}`",
            f"- Max absolute error: `{values.get('max_absolute_error')}`",
            "",
        ])

    return "\n".join(lines)


def export_prediction(report: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    """Export prediction benchmark."""
    target = Path(output_dir)
    return {
        "prediction": write_markdown(
            target / "prediction_benchmark.md",
            build_prediction_markdown(report.get("prediction", {}) or {}),
        )
    }
