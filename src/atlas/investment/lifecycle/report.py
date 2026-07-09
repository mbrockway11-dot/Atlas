
"""Portfolio Lifecycle v2 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.lifecycle.loader import load_lifecycle_inputs
from atlas.investment.lifecycle.position_manager import build_lifecycle_rows


OUT_DIR = Path("output/investment_lifecycle")
LIFECYCLE_CSV = OUT_DIR / "position_lifecycle.csv"
REPORT_JSON = OUT_DIR / "portfolio_lifecycle_report.json"
REPORT_MD = OUT_DIR / "portfolio_lifecycle_report.md"


def build_portfolio_lifecycle_report() -> dict[str, Any]:
    inputs = load_lifecycle_inputs()
    rows = build_lifecycle_rows(inputs)

    df = pd.DataFrame(rows)
    state_counts = df["state"].value_counts().to_dict() if not df.empty and "state" in df.columns else {}

    report = {
        "success": True,
        "version": "portfolio_lifecycle_v2",
        "summary": (
            f"Portfolio Lifecycle v2 updated {len(rows)} lifecycle row(s). "
            f"States: {state_counts}."
        ),
        "position_count": int(len(rows)),
        "state_counts": state_counts,
        "lifecycle_summary": {
            "position_count": int(len(rows)),
            "state_counts": state_counts,
            "active_positions": int(state_counts.get("ACTIVE", 0)),
            "cash_positions": int(state_counts.get("CASH", 0)),
        },
        "positions": rows,
        "outputs": {
            "csv": str(LIFECYCLE_CSV),
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
        },
    }

    write_outputs(report, df)
    return report


def write_outputs(report: dict[str, Any], df: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df.to_csv(LIFECYCLE_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Portfolio Lifecycle v2 Report",
        "",
        report.get("summary", ""),
        "",
        "## Positions",
        "",
    ]

    for row in report.get("positions", []):
        lines.append(
            f"- `{row.get('asset')}` state=`{row.get('state')}` "
            f"reason=`{row.get('transition_reason')}`"
        )

    return "\\n".join(lines) + "\\n"
