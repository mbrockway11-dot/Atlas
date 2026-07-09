
"""Investment Performance v3 report/export.

Performance v3 reads Mark-to-Market v2 and Portfolio State v3 directly.
"""

from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import pandas as pd


OUT_DIR = Path("output/investment_performance")
MTM_REPORT = Path("output/investment_mark_to_market/mark_to_market_report.json")
MTM_POSITIONS = Path("output/investment_mark_to_market/positions.csv")
MTM_EQUITY_CURVE = Path("output/investment_mark_to_market/equity_curve.csv")
PORTFOLIO_STATE = Path("output/investment_portfolio_state/portfolio_state.json")

REPORT_JSON = OUT_DIR / "performance_report.json"
REPORT_MD = OUT_DIR / "performance_report.md"
SNAPSHOTS_CSV = OUT_DIR / "performance_snapshots.csv"
ATTRIBUTION_CSV = OUT_DIR / "performance_attribution.csv"
BENCHMARK_CSV = OUT_DIR / "benchmark_tracking.csv"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def build_performance_report() -> dict[str, Any]:
    mtm = load_json(MTM_REPORT)
    portfolio = load_json(PORTFOLIO_STATE)
    positions = load_csv(MTM_POSITIONS)
    equity_curve = load_csv(MTM_EQUITY_CURVE)

    equity = mtm.get("equity_snapshot", {}) or {}
    state = portfolio.get("state", {}) or {}
    exposure = state.get("exposure", {}) or {}

    pnl = {
        "initial_equity": 100000.0,
        "current_equity": float(equity.get("equity") or 100000.0),
        "pnl": float(equity.get("pnl") or 0.0),
        "pnl_pct": float(equity.get("pnl_pct") or 0.0),
        "drawdown": float(equity.get("drawdown") or 0.0),
        "source": "mark_to_market_v2",
    }

    attribution = build_attribution(positions)
    benchmark = build_benchmark_tracking(pnl, equity_curve)

    snapshot = {
        "timestamp": datetime.now(UTC).isoformat(),
        "source": "performance_v3_mtm",
        "current_equity": pnl["current_equity"],
        "pnl": pnl["pnl"],
        "pnl_pct": pnl["pnl_pct"],
        "drawdown": pnl["drawdown"],
        "risky_weight": exposure.get("risky_weight"),
        "cash_weight": exposure.get("cash_weight"),
        "reserved_cash_weight": exposure.get("reserved_cash_weight"),
        "position_count": int(len(positions)),
    }

    report = {
        "success": True,
        "version": "performance_v3",
        "summary": (
            f"Performance v3 read MTM equity={pnl['current_equity']} "
            f"PnL={pnl['pnl']} drawdown={pnl['drawdown']}."
        ),
        "pnl": pnl,
        "positions": {
            "position_count": int(len(positions)),
            "risky_weight": exposure.get("risky_weight"),
            "cash_weight": exposure.get("cash_weight"),
            "reserved_cash_weight": exposure.get("reserved_cash_weight"),
        },
        "benchmark": benchmark,
        "attribution": attribution,
        "snapshot": snapshot,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "snapshots_csv": str(SNAPSHOTS_CSV),
            "attribution_csv": str(ATTRIBUTION_CSV),
            "benchmark_csv": str(BENCHMARK_CSV),
        },
    }

    write_outputs(report)
    return report


def build_attribution(positions: pd.DataFrame) -> list[dict]:
    if positions.empty:
        return []

    rows = []
    total_value = float(pd.to_numeric(positions.get("market_value", 0.0), errors="coerce").fillna(0.0).sum())

    for _, row in positions.iterrows():
        value = float(row.get("market_value") or 0.0)
        pnl = float(row.get("unrealized_pnl") or 0.0)

        rows.append({
            "asset": row.get("asset"),
            "side": row.get("side"),
            "quantity": row.get("quantity"),
            "avg_entry_price": row.get("avg_entry_price"),
            "current_price": row.get("current_price"),
            "market_value": round(value, 2),
            "portfolio_share": round(value / total_value, 6) if total_value else 0.0,
            "unrealized_pnl": round(pnl, 2),
            "unrealized_pnl_pct": row.get("unrealized_pnl_pct"),
            "contribution_to_pnl": round(pnl, 2),
        })

    return rows


def build_benchmark_tracking(pnl: dict, equity_curve: pd.DataFrame) -> dict:
    rows = []

    if not equity_curve.empty:
        latest = equity_curve.tail(1).iloc[0].to_dict()
        rows.append({
            "timestamp": latest.get("timestamp"),
            "portfolio_equity": latest.get("equity"),
            "portfolio_pnl_pct": latest.get("pnl_pct"),
            "benchmark": "equal_weight_BTC_ETH_SOL",
            "benchmark_status": "placeholder_until_historical_price_index",
        })

    return {
        "benchmark": "equal_weight_BTC_ETH_SOL",
        "status": "tracking_placeholder",
        "portfolio_pnl_pct": pnl.get("pnl_pct"),
        "rows": rows,
        "note": "Benchmark series will become active once indexed BTC/ETH/SOL baseline tracking is added.",
    }


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
    pd.DataFrame(report.get("benchmark", {}).get("rows", [])).to_csv(BENCHMARK_CSV, index=False)


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Investment Performance v3 Report",
        "",
        report.get("summary", ""),
        "",
        "## PnL",
        "",
        "```json",
        json.dumps(report.get("pnl", {}), indent=2),
        "```",
        "",
        "## Attribution",
        "",
    ]

    for row in report.get("attribution", []):
        lines.append(
            f"- `{row.get('asset')}` value=`{row.get('market_value')}` "
            f"unrealized=`{row.get('unrealized_pnl')}`"
        )

    return "\n".join(lines) + "\n"
