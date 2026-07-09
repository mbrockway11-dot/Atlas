
"""Execution Planner v3 planner."""

from __future__ import annotations

import pandas as pd


def build_execution_plan(inputs: dict) -> dict:
    orders = inputs.get("rebalance_orders")
    rebalance_report = inputs.get("rebalance_report", {}) or {}

    if orders is None or orders.empty:
        return {
            "planner_status": "NO_REBALANCE_NEEDED",
            "summary": "Execution Planner v3 found no rebalance orders. Portfolio already matches target allocation.",
            "planned_orders": [],
            "counts": {
                "open_orders": 0,
                "blocked_orders": 0,
                "total_orders": 0,
            },
            "rebalance_turnover": rebalance_report.get("turnover", 0),
        }

    planned = []

    for i, row in orders.iterrows():
        planned.append({
            "asset": row.get("asset"),
            "side": row.get("side", "LONG"),
            "planned_weight": round(float(row.get("weight_delta") or 0.0), 6),
            "signed_delta": round(float(row.get("signed_delta") or 0.0), 6),
            "order_action": row.get("action"),
            "execution_gate": "OPEN",
            "priority": int(row.get("priority") or i + 1),
            "source": row.get("source", "rebalance_engine_v4"),
            "order_type": row.get("order_type", "REBALANCE_INTENT"),
            "reason": row.get("reason"),
        })

    return {
        "planner_status": "ORDERS_READY",
        "summary": f"Execution Planner v3 built {len(planned)} planned order row(s) from Rebalance Engine v4.",
        "planned_orders": planned,
        "counts": {
            "open_orders": len(planned),
            "blocked_orders": 0,
            "total_orders": len(planned),
        },
        "rebalance_turnover": rebalance_report.get("turnover", 0),
    }
