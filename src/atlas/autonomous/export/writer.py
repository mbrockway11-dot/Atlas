
"""Autonomous export writer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.autonomous.export.markdown import build_autonomous_markdown


DEFAULT_EXPORT_DIR = Path("output/autonomous")


def export_autonomous_report(
    report: dict[str, Any],
    *,
    output_dir: str | Path = DEFAULT_EXPORT_DIR,
) -> dict[str, Any]:
    """Export autonomous report as JSON and markdown."""
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    json_path = target / "autonomous_report.json"
    md_path = target / "autonomous_summary.md"
    theory_path = target / "theory_report.md"
    prediction_path = target / "prediction_benchmark.md"
    provenance_json_path = target / "provenance_report.json"
    provenance_md_path = target / "provenance_report.md"

    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    md_path.write_text(
        build_autonomous_markdown(report),
        encoding="utf-8",
    )

    theory_path.write_text(
        build_theory_markdown(report.get("theory", {}) or {}),
        encoding="utf-8",
    )

    prediction_path.write_text(
        build_prediction_markdown(report.get("prediction", {}) or {}),
        encoding="utf-8",
    )

    provenance = report.get("provenance", {}) or {}

    provenance_json_path.write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    provenance_md_path.write_text(
        build_provenance_markdown(provenance),
        encoding="utf-8",
    )

    return {
        "success": True,
        "output_dir": str(target),
        "files": {
            "json": str(json_path),
            "summary": str(md_path),
            "theory": str(theory_path),
            "prediction": str(prediction_path),
            "provenance_json": str(provenance_json_path),
            "provenance": str(provenance_md_path),
        },
    }


def build_theory_markdown(theory: dict[str, Any]) -> str:
    """Build standalone theory markdown."""
    lines = [
        "# Atlas Theory Report",
        "",
        theory.get("summary", "No theory summary available."),
        "",
        f"- Evidence count: `{theory.get('evidence_count', 0)}`",
        f"- Candidate count: `{theory.get('candidate_count', 0)}`",
        f"- Promoted count: `{theory.get('promoted_count', 0)}`",
        "",
    ]

    for item in theory.get("theories", []) or []:
        lines.extend([
            f"## {item.get('label', item.get('theory_id', 'Theory'))}",
            "",
            f"- Theory ID: `{item.get('theory_id')}`",
            f"- Status: `{item.get('status')}`",
            f"- Score: `{item.get('theory_score')}`",
            f"- Strength: `{item.get('theory_strength')}`",
            f"- Evidence count: `{item.get('evidence_count')}`",
            f"- Promotion reason: {item.get('promotion_reason')}",
            "",
        ])

    return "\n".join(lines).strip() + "\n"


def build_prediction_markdown(prediction: dict[str, Any]) -> str:
    """Build standalone prediction benchmark markdown."""
    lines = [
        "# Atlas Prediction Benchmark",
        "",
        prediction.get("summary", "No prediction summary available."),
        "",
    ]

    if not prediction.get("success"):
        return "\n".join(lines).strip() + "\n"

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

    targets = scores.get("targets", {}) or {}
    for target, values in targets.items():
        lines.extend([
            f"### {target}",
            "",
            f"- Count: `{values.get('count')}`",
            f"- Mean absolute error: `{values.get('mean_absolute_error')}`",
            f"- Max absolute error: `{values.get('max_absolute_error')}`",
            "",
        ])

    return "\n".join(lines).strip() + "\n"



def build_provenance_markdown(provenance: dict[str, Any]) -> str:
    """Build standalone provenance markdown."""
    lines = [
        "# Atlas Provenance Report",
        "",
        provenance.get("summary", "No provenance summary available."),
        "",
    ]

    graph = provenance.get("graph", {}) or {}
    graph_summary = graph.get("summary", {}) or {}

    lines.extend([
        "## Graph Summary",
        "",
        f"- Node count: `{graph_summary.get('node_count', 0)}`",
        f"- Edge count: `{graph_summary.get('edge_count', 0)}`",
        "",
        "## Object Types",
        "",
    ])

    object_types = graph_summary.get("object_types", {}) or {}

    if object_types:
        for object_type, count in object_types.items():
            lines.append(f"- `{object_type}`: `{count}`")
    else:
        lines.append("No object types available.")

    lines.extend([
        "",
        "## Registry Objects",
        "",
    ])

    registry = provenance.get("registry", {}) or {}
    objects = registry.get("objects", {}) or {}

    if objects:
        for object_id, item in objects.items():
            lines.extend([
                f"### {object_id}",
                "",
                f"- Type: `{item.get('type')}`",
                f"- Label: {item.get('label')}",
                f"- Created: `{item.get('created_at')}`",
                "",
            ])
    else:
        lines.append("No registry objects available.")
        lines.append("")

    lines.extend([
        "## Lineage Relations",
        "",
    ])

    lineage = provenance.get("lineage", {}) or {}
    relations = lineage.get("relations", []) or []

    if relations:
        for relation in relations:
            lines.append(
                f"- `{relation.get('parent')}` --{relation.get('relation')}--> `{relation.get('child')}`"
            )
    else:
        lines.append("No lineage relations available.")

    lines.append("")
    return "\\n".join(lines).strip() + "\\n"
