
"""Risk Engine aggregate scoring."""

from __future__ import annotations


RISK_WEIGHTS = {
    "exposure": 0.25,
    "concentration": 0.20,
    "drawdown": 0.20,
    "learning": 0.15,
    "action": 0.10,
    "rebalance": 0.10,
}


def aggregate_risk(risk_blocks: list[dict]) -> dict:
    total = 0.0
    warnings = []

    by_type = {}

    for block in risk_blocks:
        risk_type = block.get("risk_type")
        score = float(block.get("risk_score") or 0.0)
        weight = RISK_WEIGHTS.get(risk_type, 0.05)

        total += score * weight
        by_type[risk_type] = {
            "score": round(score, 6),
            "weight": weight,
            "weighted_score": round(score * weight, 6),
        }

        warnings.extend(block.get("warnings", []) or [])

    total = round(min(total, 1.0), 6)

    return {
        "aggregate_risk_score": total,
        "risk_label": label_risk(total),
        "risk_breakdown": by_type,
        "warnings": warnings,
        "warning_count": len(warnings),
    }


def label_risk(score: float) -> str:
    if score >= 0.70:
        return "critical_risk"
    if score >= 0.45:
        return "high_risk"
    if score >= 0.25:
        return "moderate_risk"
    if score > 0:
        return "low_risk"
    return "minimal_risk"
