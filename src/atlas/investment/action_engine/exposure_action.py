
"""Exposure-based action votes."""

from __future__ import annotations


def exposure_vote(position: dict, portfolio_state: dict) -> dict:
    state = portfolio_state.get("state", {}) or {}
    exposure = state.get("exposure", {}) or {}

    risky = float(exposure.get("risky_weight") or 0.0)

    if risky > 0.60:
        return vote("REDUCE", 0.70, "Risky exposure is above 60%.")

    if risky < 0.25:
        return vote("SCALE_IN", 0.55, "Risky exposure is below 25%.")

    return vote("HOLD", 0.60, "Risky exposure is within operating band.")


def vote(action: str, confidence: float, reason: str) -> dict:
    return {
        "source": "exposure",
        "action": action,
        "confidence": confidence,
        "reason": reason,
    }
