
"""Strategy Registry v3 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.strategy_registry.loader import load_strategy_registry_inputs
from atlas.investment.strategy_registry.registry import build_registry_state


OUT_DIR = Path("output/investment_strategy_registry")
REPORT_JSON = OUT_DIR / "strategy_registry_report.json"
REPORT_MD = OUT_DIR / "strategy_registry_report.md"
STATE_JSON = OUT_DIR / "strategy_registry_state.json"
REGISTRY_CSV = OUT_DIR / "strategy_registry.csv"


def build_strategy_registry_report() -> dict[str, Any]:
    state = build_registry_state(load_strategy_registry_inputs())

    report = {
        "success": True,
        "version": "strategy_registry_v3",
        "summary": (
            f"Strategy Registry v3 updated {len(state.get('strategies', []))} strategy row(s). "
            f"Counts: {state.get('counts', {})}."
        ),
        "text_summary": (
            f"Strategy Registry v3 updated {len(state.get('strategies', []))} strategy row(s). "
            f"Counts: {state.get('counts', {})}."
        ),
        "state": state,
        "strategies": state.get("strategies", []),
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "state_json": str(STATE_JSON),
            "registry_csv": str(REGISTRY_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    state = report.get("state", {})
    pd.DataFrame(state.get("strategies", [])).to_csv(REGISTRY_CSV, index=False)

    STATE_JSON.write_text(json.dumps(state, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Strategy Registry v3 Report",
        "",
        report.get("summary", ""),
        "",
        "## Strategies",
        "",
    ]

    for row in report.get("strategies", []):
        lines.append(
            f"- `{row.get('strategy_id')}` status=`{row.get('status')}` "
            f"confidence=`{row.get('asset_confidence')}` multiplier=`{row.get('weight_multiplier')}`"
        )

    return "\n".join(lines) + "\n"
