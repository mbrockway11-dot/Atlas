
"""Position scaling logic."""

from __future__ import annotations

import pandas as pd


def evaluate_scaling(lifecycle: pd.DataFrame, portfolio_state: dict) -> list[dict]:
    if lifecycle.empty:
        return []

    state = portfolio_state.get("state", {}) or {}
    exposure = state.get("exposure", {}) or {}
    risky_weight = float(exposure.get("risky_weight") or 0.0)

    open_positions = lifecycle[lifecycle["state"] == "OPEN"] if "state" in lifecycle.columns else pd.DataFrame()

    rows = []

    for _, row in open_positions.iterrows():
        if risky_weight < 0.40:
            action = "CAN_SCALE_IN"
            reason = "Portfolio risky exposure is below 40%."
        elif risky_weight > 0.60:
            action = "DO_NOT_SCALE"
            reason = "Portfolio risky exposure is above 60%."
        else:
            action = "HOLD_SIZE"
            reason = "Portfolio exposure is within target band."

        rows.append({
            "position_id": row.get("position_id"),
            "asset": row.get("asset"),
            "side": row.get("side"),
            "current_state": row.get("state"),
            "manager_action": action,
            "reason": reason,
        })

    return rows
