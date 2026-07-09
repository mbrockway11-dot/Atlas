
"""MTM-aware exposure risk."""

from __future__ import annotations


def exposure_risk(portfolio_state: dict, mtm_report: dict | None = None) -> dict:
    state = portfolio_state.get("state", {}) or {}
    exposure = state.get("exposure", {}) or {}
    equity = state.get("equity", {}) or {}

    mtm = (mtm_report or {}).get("equity_snapshot", {}) or {}

    risky = float(exposure.get("risky_weight") or 0.0)
    cash = float(exposure.get("cash_weight") or 0.0)
    reserved = float(exposure.get("reserved_cash_weight") or 0.0)
    gross = float(exposure.get("gross_exposure") or 0.0)
    drawdown = float(equity.get("drawdown") or mtm.get("drawdown") or 0.0)

    score = 0.0
    warnings = []

    if gross > 0.85:
        score += 0.45
        warnings.append("MTM gross exposure above 85%.")
    elif gross > 0.65:
        score += 0.25
        warnings.append("MTM gross exposure above 65%.")

    if cash < 0.15:
        score += 0.30
        warnings.append("MTM cash reserve below 15%.")
    elif cash < 0.25:
        score += 0.15
        warnings.append("MTM cash reserve below 25%.")

    if reserved > 0.15:
        score += 0.10
        warnings.append("Reserved cash above 15%.")

    if drawdown < -0.10:
        score += 0.25
        warnings.append("Drawdown below -10%.")

    return {
        "risk_type": "exposure",
        "risk_score": round(min(score, 1.0), 6),
        "risky_weight": risky,
        "cash_weight": cash,
        "reserved_cash_weight": reserved,
        "gross_exposure": gross,
        "drawdown": drawdown,
        "source": "portfolio_state_v3_mtm",
        "warnings": warnings,
    }
