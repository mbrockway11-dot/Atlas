
"""Signal-based action votes."""

from __future__ import annotations


def decision_alignment_vote(position: dict, decision: dict) -> dict:
    risk = decision.get("risk_adjusted_decision", {}) or {}
    direction = str(risk.get("final_direction") or "CASH").upper()
    confidence = float(risk.get("final_confidence") or 0.0)

    side = str(position.get("side") or "").upper()

    if direction == "CASH":
        return vote("EXIT_REVIEW", 0.75, "Decision Engine moved to cash.")

    if direction == "LONG" and side == "LONG":
        if confidence >= 0.85:
            return vote("HOLD", 0.90, "Position aligns with strong long decision.")
        return vote("HOLD", 0.70, "Position aligns with current long decision.")

    if direction == "SHORT" and side == "SHORT":
        return vote("HOLD", 0.80, "Position aligns with current short decision.")

    if direction in {"LONG", "SHORT"} and side not in {direction, "CASH"}:
        return vote("EXIT_REVIEW", 0.85, "Position side conflicts with current decision.")

    return vote("HOLD", 0.50, "No strong decision conflict.")


def vote(action: str, confidence: float, reason: str) -> dict:
    return {
        "source": "decision_alignment",
        "action": action,
        "confidence": confidence,
        "reason": reason,
    }
