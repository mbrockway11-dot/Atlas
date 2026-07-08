
"""Alpha validation confidence scoring."""

from __future__ import annotations

from typing import Any


def build_alpha_confidence(validation: dict[str, Any]) -> dict[str, Any]:
    rolling = validation.get("rolling", {}).get("stability_score", 0.0)
    regime = validation.get("regime", {}).get("regime_score", 0.5)
    outlier = validation.get("outliers", {}).get("outlier_score", 0.0)
    robust = validation.get("robustness", {}).get("robustness_score", 0.0)

    score = (
        rolling * 0.30
        + regime * 0.20
        + outlier * 0.20
        + robust * 0.30
    )

    return {
        "success": True,
        "alpha_confidence": round(float(score), 6),
        "confidence_label": label(score),
        "components": {
            "rolling_stability": rolling,
            "regime_score": regime,
            "outlier_score": outlier,
            "robustness_score": robust,
        },
    }


def label(score: float) -> str:
    if score >= 0.90:
        return "elite_alpha_candidate"
    if score >= 0.80:
        return "strong_alpha_candidate"
    if score >= 0.70:
        return "promising_alpha_candidate"
    if score >= 0.60:
        return "experimental_alpha_candidate"
    return "reject_alpha_candidate"
