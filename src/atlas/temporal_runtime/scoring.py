"""Temporal runtime scoring utilities."""

from __future__ import annotations

from typing import Any


SCORING_VERSION = "0.1"


def score_transit_activation(
    transit_summary: dict[str, Any],
) -> dict[str, Any]:
    """Compute deterministic activation score from transit summary."""
    same_sign_count = int(transit_summary.get("same_sign_count", 0))
    opposition_count = int(transit_summary.get("opposition_count", 0))
    contact_count = int(transit_summary.get("contact_count", 0))

    base_score = same_sign_count * 5.0
    pressure_score = opposition_count * 3.0
    density_score = contact_count / 10.0

    activation_score = base_score + pressure_score + density_score

    return {
        "version": SCORING_VERSION,
        "activation_score": activation_score,
        "components": {
            "same_sign_score": base_score,
            "opposition_score": pressure_score,
            "density_score": density_score,
        },
        "inputs": {
            "same_sign_count": same_sign_count,
            "opposition_count": opposition_count,
            "contact_count": contact_count,
        },
        "score_status": "computed",
    }