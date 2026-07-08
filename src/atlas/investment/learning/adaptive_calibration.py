
"""Adaptive calibration recommendations."""

from __future__ import annotations


def build_calibration_recommendations(scorecard: list[dict], regime: dict) -> list[str]:
    recs = []

    if regime.get("learning_regime") == "insufficient_history":
        recs.append("Accumulate more paper-trading history before changing strategy weights.")

    if regime.get("learning_regime") == "deteriorating":
        recs.append("Reduce total exposure until paper equity trend stabilizes.")

    if regime.get("learning_regime") == "improving":
        recs.append("Maintain current risk settings; do not increase leverage until live safety governor exists.")

    high_cost = [r for r in scorecard if float(r.get("total_cost_drag") or 0.0) > 0.005]
    if high_cost:
        recs.append("Review slippage/fee assumptions for high-cost assets.")

    if not recs:
        recs.append("No calibration change recommended.")

    return recs
