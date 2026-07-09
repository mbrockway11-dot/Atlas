
"""Concentration risk."""

from __future__ import annotations


def concentration_risk(portfolio_state: dict) -> dict:
    state = portfolio_state.get("state", {}) or {}
    holdings = state.get("holdings", []) or []

    risky = [
        h for h in holdings
        if h.get("asset") not in {"CASH", "RESERVED_CASH"}
    ]

    if not risky:
        return {
            "risk_type": "concentration",
            "risk_score": 0.0,
            "max_position_weight": 0.0,
            "asset_count": 0,
            "warnings": ["No risky positions."],
        }

    weights = [abs(float(h.get("paper_weight") or 0.0)) for h in risky]
    max_weight = max(weights)
    asset_count = len(risky)

    score = 0.0
    warnings = []

    if max_weight > 0.35:
        score += 0.40
        warnings.append("Single position above 35%.")
    elif max_weight > 0.25:
        score += 0.20
        warnings.append("Single position above 25%.")

    if asset_count < 2:
        score += 0.25
        warnings.append("Fewer than 2 risky positions.")

    return {
        "risk_type": "concentration",
        "risk_score": round(min(score, 1.0), 6),
        "max_position_weight": round(float(max_weight), 6),
        "asset_count": asset_count,
        "warnings": warnings,
    }
