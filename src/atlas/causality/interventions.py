
"""Causal intervention simulation."""

from __future__ import annotations

from typing import Any


def simulate_interventions(
    records: list[dict[str, Any]],
    scan_results: list[dict[str, Any]],
    *,
    intervention_delta: float = 0.10,
) -> list[dict[str, Any]]:
    """Simulate simple directional interventions on candidate causes."""
    outputs = []

    for result in scan_results:
        correlation = float(result.get("correlation") or 0.0)

        if result.get("strength") == "insufficient_sample":
            expected_shift = 0.0
        else:
            expected_shift = correlation * intervention_delta

        outputs.append(
            {
                "candidate_id": result.get("candidate_id"),
                "cause": result.get("cause"),
                "effect": result.get("effect"),
                "intervention": f"increase {result.get('cause')} by {intervention_delta}",
                "expected_effect_shift": round(expected_shift, 6),
                "interpretation": intervention_interpretation(expected_shift),
            }
        )

    return outputs


def intervention_interpretation(expected_shift: float) -> str:
    """Interpret simulated intervention."""
    if expected_shift >= 0.07:
        return "Intervention is expected to meaningfully increase the effect."
    if expected_shift >= 0.025:
        return "Intervention may modestly increase the effect."
    if expected_shift <= -0.07:
        return "Intervention is expected to meaningfully decrease the effect."
    if expected_shift <= -0.025:
        return "Intervention may modestly decrease the effect."
    return "Intervention effect is expected to be minimal or uncertain."
