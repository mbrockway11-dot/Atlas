
"""Action and rebalance risk."""

from __future__ import annotations


def action_risk(action_engine: dict) -> dict:
    actions = action_engine.get("actions", []) or []

    score = 0.0
    warnings = []

    exit_count = sum(1 for a in actions if a.get("final_action") == "EXIT_REVIEW")
    reduce_count = sum(1 for a in actions if a.get("final_action") == "REDUCE")
    scale_count = sum(1 for a in actions if a.get("final_action") == "SCALE_IN")

    if exit_count:
        score += 0.35
        warnings.append(f"{exit_count} position(s) require exit review.")

    if reduce_count:
        score += 0.25
        warnings.append(f"{reduce_count} position(s) recommend reduction.")

    if scale_count:
        score += 0.10
        warnings.append(f"{scale_count} position(s) recommend scale-in.")

    return {
        "risk_type": "action",
        "risk_score": round(min(score, 1.0), 6),
        "exit_review_count": exit_count,
        "reduce_count": reduce_count,
        "scale_in_count": scale_count,
        "warnings": warnings,
    }


def rebalance_risk(rebalance: dict) -> dict:
    turnover = float(rebalance.get("total_turnover") or 0.0)
    order_count = int(rebalance.get("order_count") or 0)

    score = 0.0
    warnings = []

    if turnover > 0.25:
        score += 0.50
        warnings.append("Rebalance turnover above 25%.")
    elif turnover > 0.15:
        score += 0.25
        warnings.append("Rebalance turnover above 15%.")

    if order_count > 5:
        score += 0.25
        warnings.append("Rebalance order count above 5.")

    return {
        "risk_type": "rebalance",
        "risk_score": round(min(score, 1.0), 6),
        "turnover": turnover,
        "order_count": order_count,
        "warnings": warnings,
    }
