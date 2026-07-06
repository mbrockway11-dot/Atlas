
"""Candidate causal model generation."""

from __future__ import annotations

from typing import Any


DEFAULT_CAUSAL_CANDIDATES = [
    {
        "candidate_id": "recurrence_drives_recovery",
        "cause": "dynamics.dynamic_profile.recurrence",
        "effect": "dynamics.prediction.recovery_probability",
        "claim": "Recurrence may stabilize recovery probability.",
        "mechanism": "Repeated return to attractor nodes may create stable recovery basins.",
    },
    {
        "candidate_id": "energy_drives_sensitivity",
        "cause": "dynamics.dynamic_profile.mean_energy",
        "effect": "dynamics.prediction.perturbation_sensitivity",
        "claim": "Transition energy may increase perturbation sensitivity.",
        "mechanism": "Higher movement cost may make the field more reactive under external pressure.",
    },
    {
        "candidate_id": "attractors_drive_recovery",
        "cause": "dynamics.dynamic_profile.attractor_density",
        "effect": "dynamics.prediction.recovery_probability",
        "claim": "Attractor density may support recovery.",
        "mechanism": "More stable basins give the system more paths back to coherence.",
    },
    {
        "candidate_id": "field_complexity_drives_sensitivity",
        "cause": "dynamics.dynamic_profile.field_edge_count",
        "effect": "dynamics.prediction.perturbation_sensitivity",
        "claim": "Field complexity may increase perturbation sensitivity.",
        "mechanism": "More directed currents create more possible activation paths under pressure.",
    },
]


def build_candidate_models(extra_candidates: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Build candidate causal model list."""
    models = list(DEFAULT_CAUSAL_CANDIDATES)

    if extra_candidates:
        models.extend(extra_candidates)

    return models
