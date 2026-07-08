
"""Strategy Registry report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.strategy_registry.registry import build_strategy_registry


OUT_DIR = Path("output/investment_strategy_registry")
SIGNALS_CSV = OUT_DIR / "strategy_registry_signals.csv"
REPORT_JSON = OUT_DIR / "strategy_registry_report.json"
REPORT_MD = OUT_DIR / "strategy_registry_report.md"


def build_strategy_registry_report() -> dict[str, Any]:
    report = build_strategy_registry()
    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(report.get("signals", [])).to_csv(SIGNALS_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Strategy Registry Report",
        "",
        report.get("text_summary", ""),
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(report.get("summary", {}), indent=2, default=str),
        "```",
        "",
        "## Signals",
        "",
    ]

    for row in report.get("signals", []) or []:
        lines.append(
            f"- `{row.get('source')}` / `{row.get('strategy_id')}` "
            f"asset=`{row.get('asset')}` action=`{row.get('action')}` "
            f"direction=`{row.get('direction')}` exposure=`{row.get('target_exposure')}`"
        )

    return "\n".join(lines) + "\n"
