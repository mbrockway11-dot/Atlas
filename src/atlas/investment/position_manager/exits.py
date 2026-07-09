
"""Position exit evaluation."""

from __future__ import annotations

import pandas as pd


def evaluate_exits(lifecycle: pd.DataFrame, decision: dict, learning: dict) -> list[dict]:
    if lifecycle.empty:
        return []

    risk = decision.get("risk_adjusted_decision", {}) or {}
    final_direction = str(risk.get("final_direction") or "CASH").upper()

    learning_regime = (learning.get("learning_regime", {}) or {}).get("learning_regime")

    open_positions = lifecycle[lifecycle["state"] == "OPEN"] if "state" in lifecycle.columns else pd.DataFrame()

    rows = []

    for _, row in open_positions.iterrows():
        side = str(row.get("side") or "").upper()

        action = "HOLD"
        reason = "No exit condition triggered."

        if learning_regime == "deteriorating":
            action = "REDUCE"
            reason = "Learning regime is deteriorating."
        elif final_direction == "CASH":
            action = "EXIT_REVIEW"
            reason = "Decision Engine moved to cash."
        elif final_direction == "LONG" and side == "SHORT":
            action = "EXIT_REVIEW"
            reason = "Position side conflicts with current long bias."
        elif final_direction == "SHORT" and side == "LONG":
            action = "EXIT_REVIEW"
            reason = "Position side conflicts with current short bias."

        rows.append({
            "position_id": row.get("position_id"),
            "asset": row.get("asset"),
            "side": row.get("side"),
            "current_state": row.get("state"),
            "manager_action": action,
            "reason": reason,
        })

    return rows
