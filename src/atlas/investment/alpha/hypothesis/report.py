
"""Alpha Hypothesis Generator report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.investment.alpha.hypothesis.generator import build_alpha_hypotheses


OUT_DIR = Path("output/investment_alpha")
HYPOTHESES_JSON = OUT_DIR / "alpha_hypotheses.json"
HYPOTHESES_MD = OUT_DIR / "alpha_hypotheses.md"


def build_alpha_hypothesis_report(max_per_family: int = 25) -> dict[str, Any]:
    """Build and export Alpha Hypothesis report."""
    report = build_alpha_hypotheses(max_per_family=max_per_family)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    HYPOTHESES_JSON.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    HYPOTHESES_MD.write_text(
        build_markdown(report),
        encoding="utf-8",
    )

    report["json_path"] = str(HYPOTHESES_JSON)
    report["markdown_path"] = str(HYPOTHESES_MD)
    return report


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Alpha Hypothesis Generator",
        "",
        report.get("summary", report.get("error", "")),
        "",
        "## Families",
        "",
    ]

    for family, count in (report.get("families", {}) or {}).items():
        lines.append(f"- `{family}`: `{count}`")

    lines.extend(["", "## Hypotheses", ""])

    for h in report.get("hypotheses", []) or []:
        lines.extend([
            f"### {h.get('hypothesis_id')}",
            "",
            f"- Family: `{h.get('family')}`",
            f"- Direction: `{h.get('direction')}`",
            f"- Hold period: `{h.get('hold_period')}`",
            f"- Signal asset rule: `{h.get('signal_asset_rule')}`",
            f"- Rank score: `{h.get('rank_score')}`",
            "",
            h.get("description", ""),
            "",
            "Conditions:",
        ])

        for c in h.get("conditions", []) or []:
            lines.append(
                f"- `{c.get('source')}.{c.get('feature')}` {c.get('op')} `{c.get('value')}`"
            )

        lines.append("")

    return "\n".join(lines)
