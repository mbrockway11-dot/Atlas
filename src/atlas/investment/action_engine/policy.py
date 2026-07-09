
"""Action Engine v3 policy layer."""

from __future__ import annotations


EXECUTABLE_ACTIONS = {
    "REQUEST_CLOSE",
    "REQUEST_REDUCE",
    "REQUEST_TAKE_PROFIT",
    "UPDATE_TRAILING_STOP",
    "REQUEST_EXIT_REVIEW",
}


def apply_action_policy(action: dict) -> dict:
    out = dict(action)
    portfolio_action = out.get("portfolio_action")

    if portfolio_action in EXECUTABLE_ACTIONS:
        out["action_status"] = "ACTIONABLE"
    elif portfolio_action == "HOLD_POSITION":
        out["action_status"] = "HOLD"
    else:
        out["action_status"] = "NO_ACTION"

    if portfolio_action == "REQUEST_CLOSE":
        out["execution_instruction"] = "Generate close order through Execution Planner v2."
    elif portfolio_action == "REQUEST_REDUCE":
        out["execution_instruction"] = "Generate partial reduce order through Execution Planner v2."
    elif portfolio_action == "REQUEST_TAKE_PROFIT":
        out["execution_instruction"] = "Generate partial take-profit order through Execution Planner v2."
    elif portfolio_action == "UPDATE_TRAILING_STOP":
        out["execution_instruction"] = "Update trailing stop state; no broker order yet."
    elif portfolio_action == "REQUEST_EXIT_REVIEW":
        out["execution_instruction"] = "Flag for exit review; no broker order yet."
    else:
        out["execution_instruction"] = "Hold position."

    return out
