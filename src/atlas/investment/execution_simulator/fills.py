
"""Execution fill model."""

from __future__ import annotations

import pandas as pd

from atlas.investment.execution_simulator.costs import estimate_cost


def simulate_fills(order_intents: pd.DataFrame) -> pd.DataFrame:
    """Simulate fills from execution order intents."""
    if order_intents.empty:
        return pd.DataFrame()

    rows = []

    for _, row in order_intents.iterrows():
        asset = row.get("asset")
        action = str(row.get("order_action") or "NO_ORDER").upper()
        planned_weight = float(row.get("planned_weight") or 0.0)
        gate = row.get("execution_gate")
        side = row.get("side")

        if action in {"BUY", "SELL_SHORT"}:
            fill_status = "FILLED_SIMULATED"
            fill_weight = planned_weight
        elif action == "WAIT":
            fill_status = "WAITING_FOR_CONFIRMATION"
            fill_weight = 0.0
        else:
            fill_status = "NO_FILL"
            fill_weight = planned_weight if asset == "CASH" else 0.0

        costs = estimate_cost(fill_weight) if fill_status == "FILLED_SIMULATED" else estimate_cost(0.0)

        rows.append({
            "asset": asset,
            "side": side,
            "order_action": action,
            "execution_gate": gate,
            "planned_weight": round(float(planned_weight), 6),
            "simulated_fill_weight": round(float(fill_weight), 6),
            "fill_status": fill_status,
            "fee_drag": costs["fee_drag"],
            "slippage_drag": costs["slippage_drag"],
            "total_cost_drag": costs["total_cost_drag"],
            "reason": row.get("reason"),
        })

    return pd.DataFrame(rows)
