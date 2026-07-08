
"""Execution Simulator core."""

from __future__ import annotations

import pandas as pd

from atlas.investment.execution_simulator.fills import simulate_fills


def simulate_execution(order_intents: pd.DataFrame) -> dict:
    fills = simulate_fills(order_intents)

    if fills.empty:
        return {
            "success": False,
            "fills": [],
            "summary": {
                "filled_weight": 0.0,
                "cash_weight": 1.0,
                "total_cost_drag": 0.0,
                "warning_count": 1,
                "warnings": ["No order intents found."],
            },
        }

    filled = fills[fills["fill_status"] == "FILLED_SIMULATED"]
    waiting = fills[fills["fill_status"] == "WAITING_FOR_CONFIRMATION"]
    cash = fills[fills["asset"] == "CASH"]

    filled_weight = float(filled["simulated_fill_weight"].sum()) if not filled.empty else 0.0
    cash_weight = float(cash["planned_weight"].sum()) if not cash.empty else max(0.0, 1.0 - filled_weight)
    waiting_weight = float(waiting["planned_weight"].sum()) if not waiting.empty else 0.0
    total_cost = float(fills["total_cost_drag"].sum()) if "total_cost_drag" in fills.columns else 0.0

    warnings = []

    if waiting_weight > 0:
        warnings.append(f"{waiting_weight:.6f} planned weight is waiting for confirmation.")

    if filled_weight > 0.80:
        warnings.append("Simulated filled exposure exceeds 80%.")

    if cash_weight < 0.10:
        warnings.append("Cash reserve below 10%.")

    summary = {
        "filled_weight": round(filled_weight, 6),
        "cash_weight": round(cash_weight, 6),
        "waiting_weight": round(waiting_weight, 6),
        "total_cost_drag": round(total_cost, 8),
        "filled_count": int(len(filled)),
        "waiting_count": int(len(waiting)),
        "warning_count": int(len(warnings)),
        "warnings": warnings,
    }

    return {
        "success": True,
        "fills": fills.to_dict("records"),
        "summary": summary,
    }
