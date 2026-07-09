
"""Position Manager action votes."""

from __future__ import annotations


def position_manager_votes(position: dict, position_manager: dict) -> list[dict]:
    actions = position_manager.get("actions", []) or []
    pid = position.get("position_id")

    matched = [a for a in actions if a.get("position_id") == pid]

    votes = []

    for row in matched:
        action = str(row.get("manager_action") or "HOLD").upper()

        if action in {"HOLD", "HOLD_SIZE"}:
            mapped = "HOLD"
        elif action == "CAN_SCALE_IN":
            mapped = "SCALE_IN"
        elif action in {"REDUCE"}:
            mapped = "REDUCE"
        elif action in {"EXIT_REVIEW"}:
            mapped = "EXIT_REVIEW"
        elif action in {"TRAILING_STOP_PENDING"}:
            mapped = "TRAILING_STOP_PENDING"
        else:
            mapped = "HOLD"

        votes.append({
            "source": "position_manager",
            "action": mapped,
            "confidence": 0.70,
            "reason": row.get("reason", "Position Manager recommendation."),
        })

    if not votes:
        votes.append({
            "source": "position_manager",
            "action": "HOLD",
            "confidence": 0.50,
            "reason": "No Position Manager action found.",
        })

    return votes
