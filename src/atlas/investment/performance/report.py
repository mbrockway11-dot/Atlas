
"""Performance Engine v3 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.performance.attribution import exposure_summary, position_attribution
from atlas.investment.performance.benchmark import benchmark_tracking
from atlas.investment.performance.loader import load_performance_inputs
from atlas.investment.performance.metrics import cost_metrics, equity_metrics, trade_metrics


OUT_DIR = Path("output/investment_performance")
REPORT_JSON = OUT_DIR / "performance_report.json"
REPORT_MD = OUT_DIR / "performance_report.md"
SNAPSHOTS_CSV = OUT_DIR / "performance_snapshots.csv"
ATTRIBUTION_CSV = OUT_DIR / "performance_attribution.csv"
BENCHMARK_CSV = OUT_DIR / "benchmark_tracking.csv"


def build_performance_report() -> dict[str, Any]:
    inputs = load_performance_inputs()

    equity = equity_metrics(inputs["equity_curve"])
    trades = trade_metrics(inputs["broker_fills"])
    costs = cost_metrics(inputs["broker_fills"])
    attribution = position_attribution(inputs["positions"])
    exposure = exposure_summary(inputs["positions"], inputs["mtm_report"])
    benchmark = benchmark_tracking(inputs["equity_curve"])

    report = {
        "success": True,
        "version": "performance_engine_v3",
        "summary": (
            f"Performance Engine v3 read broker/MTM state. "
            f"Equity={equity['current_equity']}, PnL={equity['pnl']}, "
            f"Sharpe={equity['sharpe']}, MaxDD={equity['max_drawdown']}."
        ),
        "pnl": {
            "initial_equity": equity["start_equity"],
            "current_equity": equity["current_equity"],
            "pnl": equity["pnl"],
            "pnl_pct": equity["pnl_pct"],
            "drawdown": equity["max_drawdown"],
            "source": "mark_to_market_v3",
        },
        "equity_metrics": equity,
        "trade_metrics": trades,
        "cost_metrics": costs,
        "exposure": exposure,
        "positions": attribution,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "snapshots_csv": str(SNAPSHOTS_CSV),
            "attribution_csv": str(ATTRIBUTION_CSV),
            "benchmark_csv": str(BENCHMARK_CSV),
        },
    }

    write_outputs(report, attribution, benchmark)
    return report


def write_outputs(report: dict[str, Any], attribution: list[dict], benchmark: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame([{
        **report.get("equity_metrics", {}),
        **report.get("trade_metrics", {}),
        **report.get("cost_metrics", {}),
        **report.get("exposure", {}),
    }]).to_csv(SNAPSHOTS_CSV, index=False)

    pd.DataFrame(attribution).to_csv(ATTRIBUTION_CSV, index=False)
    benchmark.to_csv(BENCHMARK_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Performance Engine v3 Report",
        "",
        report.get("summary", ""),
        "",
        "## Equity Metrics",
        "",
        "```json",
        json.dumps(report.get("equity_metrics", {}), indent=2),
        "```",
        "",
        "## Trade Metrics",
        "",
        "```json",
        json.dumps(report.get("trade_metrics", {}), indent=2),
        "```",
        "",
        "## Positions",
        "",
    ]

    for row in report.get("positions", []):
        lines.append(
            f"- `{row.get('asset')}` value=`{row.get('market_value')}` pnl=`{row.get('unrealized_pnl')}`"
        )

    return "\n".join(lines) + "\n"
