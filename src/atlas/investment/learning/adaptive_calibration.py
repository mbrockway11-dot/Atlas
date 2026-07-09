
"""Learning v2 adaptive calibration recommendations."""

from __future__ import annotations


def build_calibration_recommendations(scorecard: list[dict], regime: dict) -> list[str]:
    recs = []

    state = regime.get("learning_regime")

    if state == "insufficient_history":
        recs.append("Accumulate more MTM equity history before changing adaptive weights.")
    elif state == "deteriorating":
        recs.append("Reduce total exposure and tighten safety gates until MTM equity stabilizes.")
    elif state == "improving":
        recs.append("Maintain current risk settings; do not increase live risk until paper validation period completes.")
    elif state == "flat":
        recs.append("Maintain current exposure while monitoring MTM equity curve for directional evidence.")

    underperformers = [r for r in scorecard if r.get("status") == "underperforming"]
    outperformers = [r for r in scorecard if r.get("status") == "outperforming"]

    if underperformers:
        assets = ", ".join(str(r.get("asset")) for r in underperformers)
        recs.append(f"Review underperforming assets for reduced allocation: {assets}.")

    if outperformers:
        assets = ", ".join(str(r.get("asset")) for r in outperformers)
        recs.append(f"Continue monitoring outperforming assets before increasing weights: {assets}.")

    if not recs:
        recs.append("No calibration change recommended.")

    return recs
