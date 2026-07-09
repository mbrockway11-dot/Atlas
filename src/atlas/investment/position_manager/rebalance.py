
"""Position rebalance evaluation."""

from __future__ import annotations

import pandas as pd


def evaluate_rebalance(lifecycle: pd.DataFrame, portfolio_state: dict) -> dict:
    state = portfolio_state.get("state", {}) or {}
    exposure = state.get("exposure", {}) or {}

    risky = float(exposure.get("risky_weight") or 0.0)
    reserved = float(exposure.get("reserved_cash_weight") or 0.0)
    cash = float(exposure.get("cash_weight") or 0.0)

    if reserved > 0.10:
        action = "REVIEW_RESERVED_CASH"
        reason = "Reserved cash exceeds 10%; check pending execution confirmations."
    elif risky < 0.25:
        action = "UNDER_ALLOCATED"
        reason = "Risky exposure is below 25%."
    elif risky > 0.60:
        action = "OVER_ALLOCATED"
        reason = "Risky exposure is above 60%."
    else:
        action = "BALANCED"
        reason = "Portfolio allocation is within operating band."

    return {
        "manager_action": action,
        "reason": reason,
        "risky_weight": risky,
        "reserved_cash_weight": reserved,
        "cash_weight": cash,
    }
