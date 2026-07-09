
"""Execution Engine v3 simulated fill logic."""

from __future__ import annotations

from datetime import datetime, UTC

from atlas.investment.execution_engine.costs import estimate_costs


def simulate_execution(order: dict) -> dict:
    out = dict(order)

    if out.get("execution_status") != "QUEUED":
        out.update({
            "fill_status": "NO_FILL",
            "filled_weight": 0.0,
            "fill_timestamp": None,
        })
        return out

    costs = estimate_costs(out)
    requested = float(out.get("requested_weight") or 0.0)
    filled = max(0.0, requested - costs["total_cost_drag"])

    out.update(costs)
    out.update({
        "execution_status": "EXECUTED_SIMULATED",
        "fill_status": "FILLED_SIMULATED",
        "filled_weight": round(filled, 6),
        "fill_timestamp": datetime.now(UTC).isoformat(),
        "broker_route": "paper_broker_v3_ready",
    })

    return out
