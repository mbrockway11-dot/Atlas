
"""Autonomous report markdown export."""

from __future__ import annotations

from typing import Any


def build_autonomous_markdown(report: dict[str, Any]) -> str:
    """Build markdown summary from autonomous report."""
    learning = report.get("learning_update", {}) or {}
    theory = report.get("theory", {}) or {}
    prediction = report.get("prediction", {}) or {}
    falsification = report.get("falsification", {}) or {}
    evidence = report.get("evidence_registry", {}) or {}

    lines = [
        "# Atlas Autonomous Research Report",
        "",
        "## Summary",
        "",
        report.get("summary", "No summary available."),
        "",
        "## Learning",
        "",
        f"- Learning label: `{learning.get('learning_label', 'n/a')}`",
        f"- Learning score: `{learning.get('learning_score', 'n/a')}`",
        f"- Signals integrated: `{learning.get('signal_count', 0)}`",
        "",
        "## Evidence",
        "",
        f"- Evidence records: `{len(evidence.get('records', {}) or {})}`",
        f"- Evidence relations: `{len(evidence.get('relations', []) or [])}`",
        "",
        "## Theory",
        "",
        theory.get("summary", "No theory summary available."),
        "",
        f"- Candidates: `{theory.get('candidate_count', 0)}`",
        f"- Promoted: `{theory.get('promoted_count', 0)}`",
        "",
        "## Falsification",
        "",
        falsification.get("summary", "No falsification summary available."),
        "",
        "## Prediction",
        "",
        prediction.get("summary", "No prediction summary available."),
        "",
    ]

    scores = ((prediction.get("benchmark", {}) or {}).get("scores", {}) or {})
    if scores:
        lines.extend([
            f"- Mean absolute error: `{scores.get('mean_absolute_error')}`",
            f"- Max absolute error: `{scores.get('max_absolute_error')}`",
            f"- Accuracy label: `{scores.get('accuracy_label')}`",
            "",
        ])

    lines.extend(build_theory_section(theory))
    lines.extend(build_signal_section(learning))

    return "\n".join(lines).strip() + "\n"


def build_theory_section(theory: dict[str, Any]) -> list[str]:
    """Build theory markdown section."""
    lines = ["## Theory Details", ""]

    theories = theory.get("theories", []) or []

    if not theories:
        lines.append("No theories available.")
        lines.append("")
        return lines

    for item in theories:
        lines.extend([
            f"### {item.get('label', item.get('theory_id', 'Theory'))}",
            "",
            f"- ID: `{item.get('theory_id')}`",
            f"- Status: `{item.get('status')}`",
            f"- Score: `{item.get('theory_score')}`",
            f"- Strength: `{item.get('theory_strength')}`",
            f"- Evidence count: `{item.get('evidence_count')}`",
            "",
        ])

    return lines


def build_signal_section(learning: dict[str, Any]) -> list[str]:
    """Build learning signal section."""
    lines = ["## Learning Signals", ""]

    signals = learning.get("signals", []) or []

    if not signals:
        lines.append("No learning signals available.")
        lines.append("")
        return lines

    for signal in signals:
        lines.append(
            f"- `{signal.get('source')}` ? {signal.get('signal')} "
            f"(strength `{signal.get('strength')}`)"
        )

    lines.append("")
    return lines
