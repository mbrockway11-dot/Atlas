
"""Execution Planner v2 order planning."""

from __future__ import annotations

import pandas as pd


def build_execution_plan_from_rebalance(rebalance_orders: pd.DataFrame, risk: dict) -> pd.DataFrame:
    if rebalance_orders.empty:
        return pd.DataFrame()

    risk_label = (risk.get("aggregate", {}) or {}).get("risk_label", "unknown")
    rows = []

    for i, row in rebalance_orders.iterrows():
        asset = row.get("asset")
        action = str(row.get("action") or "HOLD").upper()
        signed_delta = float(row.get("signed_delta") or 0.0)
        weight_delta = abs(float(row.get("weight_delta") or signed_delta))

        if action not in {"BUY", "SELL"} or weight_delta <= 0:
            order_action = "NO_ORDER"
            gate = "CLOSED"
        else:
            order_action = action
            gate = gate_for_risk(risk_label)

        rows.append({
            "asset": asset,
            "side": row.get("side", "LONG"),
            "planned_weight": round(weight_delta, 6),
            "signed_delta": round(signed_delta, 6),
            "order_action": order_action,
            "execution_gate": gate,
            "priority": int(i + 1),
            "source": "rebalance_engine_v3",
            "order_type": row.get("order_type", "REBALANCE_INTENT"),
            "risk_label": risk_label,
            "reason": row.get("reason"),
        })

    return pd.DataFrame(rows)


def gate_for_risk(risk_label: str) -> str:
    if risk_label in {"critical_risk", "high_risk"}:
        return "BLOCKED_BY_RISK"
    if risk_label == "moderate_risk":
        return "REDUCED_REVIEW"
    return "OPEN"
