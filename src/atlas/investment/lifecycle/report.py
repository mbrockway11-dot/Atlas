
"""Portfolio Lifecycle report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.lifecycle.loader import (
    load_broker_orders,
    load_lifecycle,
    load_portfolio_holdings,
)
from atlas.investment.lifecycle.position_manager import lifecycle_actions, summarize_lifecycle
from atlas.investment.lifecycle.transition import build_lifecycle_rows


OUT_DIR = Path("output/investment_lifecycle")
LIFECYCLE_CSV = OUT_DIR / "position_lifecycle.csv"
REPORT_JSON = OUT_DIR / "portfolio_lifecycle_report.json"
REPORT_MD = OUT_DIR / "portfolio_lifecycle_report.md"


def build_portfolio_lifecycle_report() -> dict[str, Any]:
    holdings = load_portfolio_holdings()
    broker_orders = load_broker_orders()
    existing = load_lifecycle()

    lifecycle = build_lifecycle_rows(holdings, broker_orders, existing)

    summary = summarize_lifecycle(lifecycle)
    actions = lifecycle_actions(lifecycle)

    report = {
        "success": True,
        "summary": (
            f"Portfolio Lifecycle updated {summary['position_count']} lifecycle row(s). "
            f"Open={summary['open_positions']}, approved={summary['approved_orders']}, "
            f"reserved={summary['reserved_positions']}."
        ),
        "lifecycle_summary": summary,
        "actions": actions,
        "positions": lifecycle.to_dict("records"),
        "outputs": {
            "csv": str(LIFECYCLE_CSV),
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
        },
    }

    write_outputs(report, lifecycle)
    return report


def write_outputs(report: dict[str, Any], lifecycle: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    lifecycle.to_csv(LIFECYCLE_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Portfolio Lifecycle Report",
        "",
        report.get("summary", ""),
        "",
        "## Actions",
        "",
    ]

    for action in report.get("actions", []):
        lines.append(f"- {action}")

    lines.extend([
        "",
        "## Positions",
        "",
    ])

    for row in report.get("positions", []):
        lines.append(
            f"- `{row.get('asset')}` side=`{row.get('side')}` "
            f"state=`{row.get('state')}` weight=`{row.get('weight')}`"
        )

    return "\n".join(lines) + "\n"
