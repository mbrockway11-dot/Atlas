
"""Rebalance Engine v3 optimizer."""

from __future__ import annotations


MAX_GROSS_EXPOSURE_BY_RISK = {
    "minimal_risk": 0.80,
    "low_risk": 0.70,
    "moderate_risk": 0.50,
    "high_risk": 0.25,
    "critical_risk": 0.0,
}


def optimize_targets(
    current: dict[str, float],
    target: dict[str, float],
    risk: dict,
) -> dict[str, float]:
    risk_label = (risk.get("aggregate", {}) or {}).get("risk_label", "low_risk")
    max_gross = MAX_GROSS_EXPOSURE_BY_RISK.get(risk_label, 0.50)

    positive_target = {k: max(0.0, float(v)) for k, v in target.items()}
    target_sum = sum(positive_target.values())

    if target_sum <= 0 or max_gross <= 0:
        return {asset: 0.0 for asset in set(current) | set(target)}

    scaled = {
        asset: round((weight / target_sum) * max_gross, 6)
        for asset, weight in positive_target.items()
    }

    for asset in current:
        scaled.setdefault(asset, 0.0)

    return scaled
