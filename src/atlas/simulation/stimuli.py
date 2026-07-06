
"""Convert environment variables into structural stimuli."""

from __future__ import annotations

from typing import Any

from atlas.simulation.environment import SimulationEnvironment, environment_to_dict


STIMULUS_MAP = {
    "time_pressure": ("constraint_pattern", "activation_driven_action"),
    "ambiguity": ("abstraction_pattern", "information_routing"),
    "complexity": ("complexity_tolerance", "cross_domain_linking", "distributed_integration"),
    "social_visibility": ("visible_authorship", "signal_amplification", "message_propagation"),
    "resource_constraints": ("constraint_pattern", "structural_selectivity"),
    "conflict": ("energy_allocation", "constraint_sensitive_execution"),
    "novelty": ("innovation_pattern", "activation_driven_action"),
    "collaboration": ("value_selection", "cross_domain_linking"),
    "competition": ("energy_allocation", "high_resolution_discrimination"),
    "uncertainty": ("internal_stabilization", "abstraction_pattern"),
    "fatigue": ("stability_seeking", "constraint_pattern"),
}


def build_stimuli(environment: SimulationEnvironment) -> dict[str, Any]:
    """Build structural stimuli from environment."""
    env = environment_to_dict(environment)
    stimuli: dict[str, float] = {}

    for variable, intensity in env.items():
        for feature in STIMULUS_MAP.get(variable, ()):
            stimuli[feature] = min(1.0, stimuli.get(feature, 0.0) + float(intensity) * 0.5)

    return {
        "environment": env,
        "stimuli": {
            feature: round(value, 6)
            for feature, value in sorted(stimuli.items())
        },
    }
