
"""Decision risk controls."""

from __future__ import annotations


def risk_adjust_decision(
    bias: str,
    evidence_confidence: float,
    market_direction: dict,
    evidence: dict | None = None,
) -> dict:
    direction_report = market_direction.get("exposure", {}) if market_direction else {}

    market_target = float(direction_report.get("target_net_exposure") or 0.0)
    direction_confidence = float(direction_report.get("direction_confidence") or 0.0)

    c = max(0.0, min(float(evidence_confidence or 0.0), 1.0))
    combined_confidence = (c * 0.60) + (direction_confidence * 0.40)

    confirmation = confirmation_adjustment(evidence or {})
    combined_confidence *= confirmation["confidence_multiplier"]

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

    target *= confirmation["exposure_multiplier"]

    return {
        "final_direction": b,
        "final_confidence": round(float(combined_confidence), 6),
        "target_net_exposure": round(float(target), 6),
        "target_cash_weight": round(float(max(0.0, 1.0 - abs(target))), 6),
        "risk_label": label_risk(target),
        "confirmation_adjustment": confirmation,
    }


def confirmation_adjustment(evidence: dict) -> dict:
    """Reduce confidence/exposure when execution engines are idle."""
    rows = evidence.get("evidence_rows", []) or []

    execution_rows = [
        r for r in rows
        if r.get("strategy_family") == "intraday_execution"
    ]

    if not execution_rows:
        return {
            "status": "no_execution_layer",
            "confidence_multiplier": 0.90,
            "exposure_multiplier": 0.90,
            "reason": "No intraday execution layer available.",
        }

    active_rows = [
        r for r in execution_rows
        if str(r.get("action", "")).upper() not in {"NO_ACTION", "WAIT"}
        and str(r.get("direction", "")).upper() not in {"FLAT", "NEUTRAL"}
    ]

    if active_rows:
        return {
            "status": "execution_confirmed",
            "confidence_multiplier": 1.00,
            "exposure_multiplier": 1.00,
            "reason": "At least one intraday execution engine confirms active structure.",
        }

    return {
        "status": "execution_idle",
        "confidence_multiplier": 0.85,
        "exposure_multiplier": 0.75,
        "reason": "Intraday execution engines are idle; reduce confidence and exposure.",
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
