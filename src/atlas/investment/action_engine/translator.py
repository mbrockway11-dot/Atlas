
"""Translate Position Manager v3 actions into executable portfolio actions."""

from __future__ import annotations


ACTION_MAP = {
    "HOLD": "HOLD_POSITION",
    "REQUEST_EXIT": "REQUEST_CLOSE",
    "REDUCE_SIZE": "REQUEST_REDUCE",
    "REDUCE_RISK": "REQUEST_REDUCE",
    "TAKE_PROFIT_REVIEW": "REQUEST_TAKE_PROFIT",
    "ACTIVATE_TRAILING_STOP": "UPDATE_TRAILING_STOP",
    "TIME_EXIT_REVIEW": "REQUEST_EXIT_REVIEW",
    "NO_ACTION": "NO_ACTION",
}


def translate_manager_action(row: dict, risk: dict) -> dict:
    manager_action = str(row.get("manager_action") or "HOLD")
    portfolio_action = ACTION_MAP.get(manager_action, "HOLD_POSITION")

    risk_label = (risk.get("aggregate", {}) or {}).get("risk_label", "unknown")
    weight = action_weight(portfolio_action, risk_label)

    return {
        "position_id": row.get("position_id"),
        "asset": row.get("asset"),
        "side": row.get("side"),
        "state": row.get("state"),
        "manager_action": manager_action,
        "portfolio_action": portfolio_action,
        "requested_weight_delta": weight,
        "priority": row.get("priority", 9),
        "risk_label": risk_label,
        "reason": row.get("reason"),
        "source": "position_manager_v3",
    }


def action_weight(portfolio_action: str, risk_label: str) -> float:
    if portfolio_action == "REQUEST_CLOSE":
        return -1.0

    if portfolio_action == "REQUEST_REDUCE":
        if risk_label in {"high_risk", "critical_risk"}:
            return -0.50
        return -0.25

    if portfolio_action == "REQUEST_TAKE_PROFIT":
        return -0.25

    return 0.0
