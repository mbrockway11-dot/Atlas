
"""Position Manager v3 rules."""

from __future__ import annotations


STOP_LOSS_PCT = -0.05
TAKE_PROFIT_PCT = 0.08
TRAILING_STOP_ACTIVATION_PCT = 0.04
MAX_HOLDING_HOURS = 24 * 14


def evaluate_position(row: dict, risk: dict, learning: dict) -> list[dict]:
    actions = []

    asset = row.get("asset")
    state = row.get("state")
    pnl_pct = float(row.get("unrealized_pnl_pct") or 0.0)
    age = row.get("holding_age_hours")
    age = float(age) if age not in [None, "", "nan"] else 0.0

    risk_label = (risk.get("aggregate", {}) or {}).get("risk_label", "unknown")
    regime = (learning.get("learning_regime", {}) or {}).get("learning_regime", "unknown")

    if state not in {"ACTIVE", "WATCH", "OPEN"}:
        return [{
            "asset": asset,
            "manager_action": "NO_ACTION",
            "reason": f"Position state {state} does not require management.",
        }]

    if pnl_pct <= STOP_LOSS_PCT:
        actions.append({
            "asset": asset,
            "manager_action": "REQUEST_EXIT",
            "reason": f"Stop loss triggered at {pnl_pct:.6f}.",
            "priority": 1,
        })

    elif pnl_pct >= TAKE_PROFIT_PCT:
        actions.append({
            "asset": asset,
            "manager_action": "TAKE_PROFIT_REVIEW",
            "reason": f"Take-profit review triggered at {pnl_pct:.6f}.",
            "priority": 2,
        })

    elif pnl_pct >= TRAILING_STOP_ACTIVATION_PCT:
        actions.append({
            "asset": asset,
            "manager_action": "ACTIVATE_TRAILING_STOP",
            "reason": f"Trailing stop eligible at {pnl_pct:.6f}.",
            "priority": 3,
        })

    if age >= MAX_HOLDING_HOURS:
        actions.append({
            "asset": asset,
            "manager_action": "TIME_EXIT_REVIEW",
            "reason": f"Holding age {age:.2f} hours exceeds max horizon.",
            "priority": 4,
        })

    if risk_label in {"high_risk", "critical_risk"}:
        actions.append({
            "asset": asset,
            "manager_action": "REDUCE_RISK",
            "reason": f"Risk Engine label is {risk_label}.",
            "priority": 2,
        })

    if regime == "deteriorating":
        actions.append({
            "asset": asset,
            "manager_action": "REDUCE_SIZE",
            "reason": "Learning regime is deteriorating.",
            "priority": 3,
        })

    if not actions:
        actions.append({
            "asset": asset,
            "manager_action": "HOLD",
            "reason": "No position management trigger fired.",
            "priority": 9,
        })

    return actions
