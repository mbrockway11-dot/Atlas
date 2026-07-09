
"""Exposure risk."""

from __future__ import annotations


def exposure_risk(portfolio_state: dict) -> dict:
    state = portfolio_state.get("state", {}) or {}
    exposure = state.get("exposure", {}) or {}

    risky = float(exposure.get("risky_weight") or 0.0)
    cash = float(exposure.get("cash_weight") or 0.0)
    reserved = float(exposure.get("reserved_cash_weight") or 0.0)
    gross = float(exposure.get("gross_exposure") or 0.0)

    score = 0.0
    warnings = []

    if gross > 0.80:
        score += 0.40
        warnings.append("Gross exposure above 80%.")
    elif gross > 0.60:
        score += 0.25
        warnings.append("Gross exposure above 60%.")

    if cash < 0.20:
        score += 0.30
        warnings.append("Cash reserve below 20%.")

    if reserved > 0.15:
        score += 0.15
        warnings.append("Reserved cash above 15%.")

    if risky < 0.10:
        score += 0.05
        warnings.append("Portfolio is materially underallocated.")

    return {
        "risk_type": "exposure",
        "risk_score": round(min(score, 1.0), 6),
        "risky_weight": risky,
        "cash_weight": cash,
        "reserved_cash_weight": reserved,
        "gross_exposure": gross,
        "warnings": warnings,
    }
