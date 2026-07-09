
"""Trade Safety Governor report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.investment.safety.kill_switch import kill_switch_active
from atlas.investment.safety.loader import load_inputs
from atlas.investment.safety.trade_gate import evaluate_trade_safety


OUT_DIR = Path("output/investment_safety")
REPORT_JSON = OUT_DIR / "trade_safety_report.json"
REPORT_MD = OUT_DIR / "trade_safety_report.md"


def build_trade_safety_report() -> dict[str, Any]:
    if kill_switch_active():
        report = {
            "success": True,
            "approved": False,
            "safety_status": "KILL_SWITCH",
            "decision": "BLOCK_EXECUTION",
            "reason": "Kill switch is active.",
            "checks": [{
                "name": "kill_switch",
                "status": "REJECT",
                "message": "Kill switch is active.",
            }],
        }
    else:
        report = evaluate_trade_safety(load_inputs())

    report["summary"] = (
        f"Trade Safety Governor status: {report.get('safety_status')}. "
        f"Decision: {report.get('decision')}. Reason: {report.get('reason')}."
    )
    report["outputs"] = {
        "json": str(REPORT_JSON),
        "markdown": str(REPORT_MD),
    }

    if not report.get("status") and report.get("safety_status"):
        report["status"] = report["safety_status"]

    if not report.get("safety_status") and report.get("status"):
        report["safety_status"] = report["status"]

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Trade Safety Governor Report",
        "",
        report.get("summary", ""),
        "",
        "## Checks",
        "",
    ]

    for c in report.get("checks", []):
        lines.append(f"- `{c.get('status')}` `{c.get('name')}` ? {c.get('message')}")

    return "\n".join(lines) + "\n"
