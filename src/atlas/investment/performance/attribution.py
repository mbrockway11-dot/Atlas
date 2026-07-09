
"""Performance Engine v3 attribution."""

from __future__ import annotations

import pandas as pd


def position_attribution(positions: pd.DataFrame) -> list[dict]:
    if positions.empty:
        return []

    rows = []
    total_pnl = pd.to_numeric(positions.get("unrealized_pnl", 0.0), errors="coerce").fillna(0.0).sum()

    for _, row in positions.iterrows():
        pnl = float(row.get("unrealized_pnl") or 0.0)
        market_value = float(row.get("market_value") or 0.0)

        rows.append({
            "asset": row.get("asset"),
            "side": row.get("side"),
            "market_value": round(market_value, 2),
            "portfolio_weight": round(float(row.get("portfolio_weight") or 0.0), 6),
            "unrealized_pnl": round(pnl, 2),
            "unrealized_pnl_pct": round(float(row.get("unrealized_pnl_pct") or 0.0), 6),
            "contribution_to_pnl": round(pnl / total_pnl, 6) if total_pnl else 0.0,
        })

    return rows


def exposure_summary(positions: pd.DataFrame, mtm_report: dict) -> dict:
    equity = (mtm_report.get("equity_snapshot", {}) or {})
    current_equity = float(equity.get("equity") or 100000.0)
    cash = float(equity.get("cash") or 0.0)
    market_value = float(equity.get("market_value") or 0.0)

    return {
        "current_equity": round(current_equity, 2),
        "cash": round(cash, 2),
        "market_value": round(market_value, 2),
        "cash_weight": round(cash / current_equity, 6) if current_equity else 0.0,
        "risky_weight": round(market_value / current_equity, 6) if current_equity else 0.0,
        "position_count": int(len(positions)) if positions is not None else 0,
    }
