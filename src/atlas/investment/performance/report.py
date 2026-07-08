
"""Investment Performance report/export."""

from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.performance.attribution import asset_attribution
from atlas.investment.performance.benchmark import benchmark_snapshot
from atlas.investment.performance.pnl import calculate_pnl
from atlas.investment.performance.portfolio_mark_to_market import mark_portfolio_to_market
from atlas.investment.performance.position_tracker import load_paper_portfolio, summarize_positions


OUT_DIR = Path("output/investment_performance")
REPORT_JSON = OUT_DIR / "performance_report.json"
REPORT_MD = OUT_DIR / "performance_report.md"
SNAPSHOTS_CSV = OUT_DIR / "performance_snapshots.csv"
ATTRIBUTION_CSV = OUT_DIR / "performance_attribution.csv"


def build_performance_report() -> dict[str, Any]:
    portfolio = load_paper_portfolio()
    marked = mark_portfolio_to_market(portfolio)

    positions = summarize_positions(marked)
    pnl = calculate_pnl(marked)
    attribution = asset_attribution(marked)
    benchmark = benchmark_snapshot()

    snapshot = {
        "timestamp": datetime.now(UTC).isoformat(),
        **positions,
        **pnl,
    }

    report = {
        "success": True,
        "summary": (
            f"Performance Engine marked {positions['position_count']} risky position(s). "
            f"Current equity: {pnl['current_equity']}. PnL: {pnl['pnl']}."
        ),
        "positions": positions,
        "pnl": pnl,
        "benchmark": benchmark,
        "attribution": attribution,
        "snapshot": snapshot,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "snapshots_csv": str(SNAPSHOTS_CSV),
            "attribution_csv": str(ATTRIBUTION_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")

    new_snapshot = pd.DataFrame([report["snapshot"]])
    if SNAPSHOTS_CSV.exists():
        old = pd.read_csv(SNAPSHOTS_CSV)
        snapshots = pd.concat([old, new_snapshot], ignore_index=True)
    else:
        snapshots = new_snapshot

    snapshots.to_csv(SNAPSHOTS_CSV, index=False)
    pd.DataFrame(report.get("attribution", [])).to_csv(ATTRIBUTION_CSV, index=False)


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Investment Performance Report",
        "",
        report.get("summary", ""),
        "",
        "## PnL",
        "",
        "```json",
        json.dumps(report.get("pnl", {}), indent=2),
        "```",
        "",
        "## Positions",
        "",
        "```json",
        json.dumps(report.get("positions", {}), indent=2),
        "```",
        "",
        "## Attribution",
        "",
    ]

    for row in report.get("attribution", []):
        lines.append(
            f"- `{row.get('asset')}` side=`{row.get('side')}` "
            f"weight=`{row.get('weight')}` value=`{row.get('value')}`"
        )

    return "\n".join(lines) + "\n"
