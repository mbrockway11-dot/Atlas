
"""Position entry evaluation."""

from __future__ import annotations

import pandas as pd


def evaluate_entries(lifecycle: pd.DataFrame, decision: dict) -> list[dict]:
    if lifecycle.empty:
        return []

    risk = decision.get("risk_adjusted_decision", {}) or {}
    direction = str(risk.get("final_direction") or "CASH").upper()
    confidence = float(risk.get("final_confidence") or 0.0)

    approved = lifecycle[lifecycle["state"] == "APPROVED"] if "state" in lifecycle.columns else pd.DataFrame()

    rows = []

    for _, row in approved.iterrows():
        action = "QUEUE_ENTRY" if direction in {"LONG", "SHORT"} and confidence >= 0.70 else "HOLD_APPROVED"

        rows.append({
            "position_id": row.get("position_id"),
            "asset": row.get("asset"),
            "side": row.get("side"),
            "current_state": row.get("state"),
            "manager_action": action,
            "confidence": confidence,
            "reason": "Decision confidence supports entry." if action == "QUEUE_ENTRY" else "Entry held until confidence improves.",
        })

    return rows
