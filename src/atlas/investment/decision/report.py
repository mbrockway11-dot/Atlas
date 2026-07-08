
"""Decision Engine report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.decision.conflict import resolve_conflict
from atlas.investment.decision.evidence import build_evidence_scores
from atlas.investment.decision.loader import load_market_direction, load_registry
from atlas.investment.decision.risk import risk_adjust_decision


OUT_DIR = Path("output/investment_decision")
REPORT_JSON = OUT_DIR / "decision_engine_report.json"
REPORT_MD = OUT_DIR / "decision_engine_report.md"
EVIDENCE_CSV = OUT_DIR / "decision_evidence.csv"


def build_decision_engine_report() -> dict[str, Any]:
    registry = load_registry()
    market_direction = load_market_direction()

    evidence = build_evidence_scores(registry)
    conflict = resolve_conflict(evidence)
    risk = risk_adjust_decision(
        conflict.get("decision_bias"),
        conflict.get("evidence_confidence"),
        market_direction,
        evidence,
    )

    report = {
        "success": True,
        "summary": (
            f"Decision Engine selected {risk['final_direction']} "
            f"with confidence {risk['final_confidence']} "
            f"and target exposure {risk['target_net_exposure']}."
        ),
        "evidence": {
            "long_evidence": evidence.get("long_evidence"),
            "short_evidence": evidence.get("short_evidence"),
            "flat_evidence": evidence.get("flat_evidence"),
            "family_weights": evidence.get("family_weights", {}),
        },
        "conflict": conflict,
        "risk_adjusted_decision": risk,
        "market_direction": market_direction.get("exposure", {}),
        "evidence_rows": evidence.get("evidence_rows", []),
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "evidence_csv": str(EVIDENCE_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(report.get("evidence_rows", [])).to_csv(EVIDENCE_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Decision Engine Report",
        "",
        report.get("summary", ""),
        "",
        "## Evidence",
        "",
        "```json",
        json.dumps(report.get("evidence", {}), indent=2),
        "```",
        "",
        "## Conflict",
        "",
        "```json",
        json.dumps(report.get("conflict", {}), indent=2),
        "```",
        "",
        "## Risk Adjusted Decision",
        "",
        "```json",
        json.dumps(report.get("risk_adjusted_decision", {}), indent=2),
        "```",
        "",
        "## Evidence Rows",
        "",
    ]

    for row in report.get("evidence_rows", []):
        lines.append(
            f"- `{row.get('source')}` / `{row.get('strategy_id')}` "
            f"asset=`{row.get('asset')}` direction=`{row.get('direction')}` "
            f"strength=`{row.get('strength')}`"
        )

    return "\n".join(lines) + "\n"
