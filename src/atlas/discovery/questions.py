
"""Discovery question generation."""

from __future__ import annotations

from typing import Any


DEFAULT_DISCOVERY_QUESTIONS = [
    {
        "question_id": "recurrence_recovery",
        "question": "Do higher-recurrence profiles show stronger recovery probability?",
        "x_field": "dynamics.dynamic_profile.recurrence",
        "y_field": "dynamics.prediction.recovery_probability",
        "kind": "numeric_correlation",
    },
    {
        "question_id": "energy_sensitivity",
        "question": "Does higher transition energy correspond to higher perturbation sensitivity?",
        "x_field": "dynamics.dynamic_profile.mean_energy",
        "y_field": "dynamics.prediction.perturbation_sensitivity",
        "kind": "numeric_correlation",
    },
    {
        "question_id": "attractor_density_recovery",
        "question": "Does attractor density correlate with recovery probability?",
        "x_field": "dynamics.dynamic_profile.attractor_density",
        "y_field": "dynamics.prediction.recovery_probability",
        "kind": "numeric_correlation",
    },
    {
        "question_id": "field_complexity_sensitivity",
        "question": "Does field current density correspond to perturbation sensitivity?",
        "x_field": "dynamics.dynamic_profile.field_edge_count",
        "y_field": "dynamics.prediction.perturbation_sensitivity",
        "kind": "numeric_correlation",
    },
    {
        "question_id": "rarity_impact",
        "question": "Do structurally rare profiles also show higher structural impact?",
        "x_field": "rarity.rarity_score",
        "y_field": "impact.impact_score",
        "kind": "numeric_correlation",
    },
]


def build_discovery_questions(extra_questions: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Build discovery question set."""
    questions = list(DEFAULT_DISCOVERY_QUESTIONS)

    if extra_questions:
        questions.extend(extra_questions)

    return questions
