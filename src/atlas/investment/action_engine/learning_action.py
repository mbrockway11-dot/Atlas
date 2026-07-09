
"""Learning-based action votes."""

from __future__ import annotations


def learning_vote(position: dict, learning: dict) -> dict:
    regime = (learning.get("learning_regime", {}) or {}).get("learning_regime")

    if regime == "deteriorating":
        return vote("REDUCE", 0.75, "Learning regime is deteriorating.")

    if regime == "improving":
        return vote("HOLD", 0.70, "Learning regime is improving.")

    if regime == "insufficient_history":
        return vote("HOLD", 0.55, "Insufficient learning history; avoid aggressive changes.")

    return vote("HOLD", 0.60, f"Learning regime is {regime}.")


def vote(action: str, confidence: float, reason: str) -> dict:
    return {
        "source": "learning",
        "action": action,
        "confidence": confidence,
        "reason": reason,
    }
