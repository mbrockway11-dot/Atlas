
"""Trailing stop placeholder."""

from __future__ import annotations

import pandas as pd


def evaluate_trailing_stops(lifecycle: pd.DataFrame) -> list[dict]:
    if lifecycle.empty or "state" not in lifecycle.columns:
        return []

    open_positions = lifecycle[lifecycle["state"] == "OPEN"]

    rows = []

    for _, row in open_positions.iterrows():
        rows.append({
            "position_id": row.get("position_id"),
            "asset": row.get("asset"),
            "manager_action": "TRAILING_STOP_PENDING",
            "reason": "Trailing stop calculation will activate after price/cost-basis tracking is added.",
        })

    return rows
