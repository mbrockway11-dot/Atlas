
"""Execution order intent generation."""

from __future__ import annotations

import pandas as pd


def build_order_intents(plan: pd.DataFrame) -> pd.DataFrame:
    """Convert execution plan rows into order intents."""
    if plan.empty:
        return pd.DataFrame()

    rows = []

    for _, row in plan.iterrows():
        asset = row.get("asset")
        planned_weight = float(row.get("planned_weight") or 0.0)
        side = row.get("side")
        gate = row.get("execution_gate", "OPEN")

        if asset == "CASH":
            order_action = "NO_ORDER"
        elif gate == "WAIT":
            order_action = "WAIT"
        elif planned_weight <= 0:
            order_action = "NO_ORDER"
        elif side == "LONG":
            order_action = "BUY"
        elif side == "SHORT":
            order_action = "SELL_SHORT"
        else:
            order_action = "NO_ORDER"

        rows.append({
            "asset": asset,
            "side": side,
            "planned_weight": planned_weight,
            "order_action": order_action,
            "execution_gate": gate,
            "priority": row.get("priority"),
            "reason": row.get("gate_reason") or row.get("reason"),
        })

    return pd.DataFrame(rows).sort_values(["priority", "asset"])
