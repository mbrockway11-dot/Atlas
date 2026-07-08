
"""Decision risk controls."""

from __future__ import annotations


def risk_adjust_decision(
    bias: str,
    evidence_confidence: float,
    market_direction: dict,
) -> dict:
    direction_report = market_direction.get("exposure", {}) if market_direction else {}

    market_target = float(direction_report.get("target_net_exposure") or 0.0)
    direction_confidence = float(direction_report.get("direction_confidence") or 0.0)

    c = max(0.0, min(float(evidence_confidence or 0.0), 1.0))
    combined_confidence = round((c * 0.60) + (direction_confidence * 0.40), 6)

    b = str(bias).upper()

    if b == "LONG":
        target = max(0.0, market_target) * combined_confidence
    elif b == "SHORT":
        target = min(0.0, market_target) * combined_confidence
        if target == 0.0:
            target = -0.20 * combined_confidence
    elif b == "NEUTRAL":
        target = 0.15 * combined_confidence
    else:
        target = 0.0

    return {
        "final_direction": b,
        "final_confidence": combined_confidence,
        "target_net_exposure": round(float(target), 6),
        "target_cash_weight": round(float(max(0.0, 1.0 - abs(target))), 6),
        "risk_label": label_risk(target),
    }


def label_risk(exposure: float) -> str:
    e = abs(float(exposure))
    if e >= 0.70:
        return "high_conviction_risk"
    if e >= 0.40:
        return "moderate_risk"
    if e > 0:
        return "light_risk"
    return "cash"
