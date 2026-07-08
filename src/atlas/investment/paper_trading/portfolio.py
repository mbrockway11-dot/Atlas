
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
        "cost_drag": 0.0,
    }])


def portfolio_from_fills(fills: pd.DataFrame, initial_equity: float = INITIAL_EQUITY) -> pd.DataFrame:
    if fills.empty:
        return build_initial_portfolio()

    rows = []
    filled_weight = 0.0
    waiting_weight = 0.0
    explicit_cash_weight = 0.0
    total_cost_drag = 0.0

    for _, row in fills.iterrows():
        asset = row.get("asset")
        planned_weight = float(row.get("planned_weight") or 0.0)
        fill_weight = float(row.get("simulated_fill_weight") or 0.0)
        side = row.get("side")
        status = row.get("fill_status")
        cost_drag = float(row.get("total_cost_drag") or 0.0)

        if asset == "CASH":
            explicit_cash_weight += planned_weight
            continue

        if status == "WAITING_FOR_CONFIRMATION":
            waiting_weight += planned_weight
            continue

        if fill_weight <= 0:
            continue

        net_weight = max(0.0, fill_weight - cost_drag)
        filled_weight += net_weight
        total_cost_drag += cost_drag

        rows.append({
            "asset": asset,
            "paper_weight": round(net_weight, 6),
            "paper_value": round(initial_equity * net_weight, 2),
            "side": side,
            "cost_drag": round(cost_drag, 8),
            "status": "OPEN_PAPER_POSITION",
        })

    if waiting_weight > 0:
        rows.append({
            "asset": "RESERVED_CASH",
            "paper_weight": round(waiting_weight, 6),
            "paper_value": round(initial_equity * waiting_weight, 2),
            "side": "CASH",
            "cost_drag": 0.0,
            "status": "PENDING_EXECUTION_RESERVE",
        })

    cash_weight = max(0.0, 1.0 - filled_weight - waiting_weight - total_cost_drag)

    # Prefer actual residual accounting over stale explicit cash from execution plan.
    rows.append({
        "asset": "CASH",
        "paper_weight": round(cash_weight, 6),
        "paper_value": round(initial_equity * cash_weight, 2),
        "side": "CASH",
        "cost_drag": 0.0,
        "status": "AVAILABLE_CASH",
    })

    return pd.DataFrame(rows)
