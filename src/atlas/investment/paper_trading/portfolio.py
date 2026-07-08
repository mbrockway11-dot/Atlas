
"""Paper portfolio state."""

from __future__ import annotations

import pandas as pd


INITIAL_EQUITY = 100000.0


def build_initial_portfolio() -> pd.DataFrame:
    return pd.DataFrame([{
        "asset": "CASH",
        "paper_weight": 1.0,
        "paper_value": INITIAL_EQUITY,
        "side": "CASH",
    }])


def portfolio_from_fills(fills: pd.DataFrame, initial_equity: float = INITIAL_EQUITY) -> pd.DataFrame:
    if fills.empty:
        return build_initial_portfolio()

    rows = []

    for _, row in fills.iterrows():
        asset = row.get("asset")
        fill_weight = float(row.get("simulated_fill_weight") or 0.0)
        side = row.get("side")
        cost_drag = float(row.get("total_cost_drag") or 0.0)

        if asset == "CASH":
            cash_weight = float(row.get("planned_weight") or 0.0)
            rows.append({
                "asset": "CASH",
                "paper_weight": round(cash_weight, 6),
                "paper_value": round(initial_equity * cash_weight, 2),
                "side": "CASH",
                "cost_drag": 0.0,
            })
            continue

        if fill_weight <= 0:
            continue

        net_weight = max(0.0, fill_weight - cost_drag)

        rows.append({
            "asset": asset,
            "paper_weight": round(net_weight, 6),
            "paper_value": round(initial_equity * net_weight, 2),
            "side": side,
            "cost_drag": round(cost_drag, 8),
        })

    used = sum(r["paper_weight"] for r in rows if r["asset"] != "CASH")
    has_cash = any(r["asset"] == "CASH" for r in rows)

    if not has_cash:
        cash_weight = max(0.0, 1.0 - used)
        rows.append({
            "asset": "CASH",
            "paper_weight": round(cash_weight, 6),
            "paper_value": round(initial_equity * cash_weight, 2),
            "side": "CASH",
            "cost_drag": 0.0,
        })

    return pd.DataFrame(rows)
