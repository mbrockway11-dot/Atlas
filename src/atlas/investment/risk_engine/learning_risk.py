
"""Learning/regime risk."""

from __future__ import annotations


def learning_risk(learning: dict) -> dict:
    regime = learning.get("learning_regime", {}) or {}
    state = regime.get("learning_regime")
    confidence = float(regime.get("confidence") or 0.0)

    score = 0.0
    warnings = []

    if state == "deteriorating":
        score = 0.70
        warnings.append("Learning regime is deteriorating.")
    elif state == "insufficient_history":
        score = 0.25
        warnings.append("Insufficient history for strong learning confidence.")
    elif state == "flat":
        score = 0.15
        warnings.append("Learning regime is flat.")
    elif state == "improving":
        score = max(0.0, 0.10 - confidence * 0.05)

    return {
        "risk_type": "learning",
        "risk_score": round(score, 6),
        "learning_regime": state,
        "learning_confidence": confidence,
        "warnings": warnings,
    }
