
"""Lifecycle position manager."""

from __future__ import annotations

import pandas as pd


def summarize_lifecycle(lifecycle: pd.DataFrame) -> dict:
    if lifecycle.empty:
        return {
            "position_count": 0,
            "state_counts": {},
            "open_positions": 0,
            "approved_orders": 0,
            "reserved_positions": 0,
        }

    state_counts = lifecycle["state"].value_counts().to_dict() if "state" in lifecycle.columns else {}

    return {
        "position_count": int(len(lifecycle)),
        "state_counts": state_counts,
        "open_positions": int(state_counts.get("OPEN", 0)),
        "approved_orders": int(state_counts.get("APPROVED", 0)),
        "reserved_positions": int(state_counts.get("RESERVED", 0)),
    }


def lifecycle_actions(lifecycle: pd.DataFrame) -> list[str]:
    if lifecycle.empty:
        return ["No lifecycle positions available."]

    actions = []

    approved = lifecycle[lifecycle["state"] == "APPROVED"] if "state" in lifecycle.columns else pd.DataFrame()
    reserved = lifecycle[lifecycle["state"] == "RESERVED"] if "state" in lifecycle.columns else pd.DataFrame()

    if not approved.empty:
        actions.append(f"{len(approved)} approved broker order(s) awaiting paper/live fill handling.")

    if not reserved.empty:
        actions.append(f"{len(reserved)} reserved cash position(s) waiting for execution confirmation.")

    if not actions:
        actions.append("No lifecycle action required.")

    return actions
