
"""Theory export."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.autonomous.export.markdown import write_markdown


def build_theory_markdown(theory: dict[str, Any]) -> str:
    """Build theory markdown."""
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
            "",
        ])

    return "\n".join(lines)


def export_theory(report: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    """Export theory report."""
    target = Path(output_dir)
    return {
        "theory": write_markdown(target / "theory_report.md", build_theory_markdown(report.get("theory", {}) or {}))
    }
