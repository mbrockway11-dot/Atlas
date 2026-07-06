
"""Autonomous experiment generation."""

from __future__ import annotations

from typing import Any


DEFAULT_VARIABLES = [
    "dynamics.dynamic_profile.recurrence",
    "dynamics.dynamic_profile.mean_energy",
    "dynamics.dynamic_profile.attractor_density",
    "dynamics.dynamic_profile.field_edge_count",
    "dynamics.prediction.recovery_probability",
    "dynamics.prediction.perturbation_sensitivity",
]


def generate_experiment_questions(
    *,
    variables: list[str] | None = None,
    max_questions: int = 25,
) -> list[dict[str, Any]]:
    """Generate candidate experiment questions from variable pairs."""
    fields = variables or DEFAULT_VARIABLES
    questions = []

    for left_index, left in enumerate(fields):
        for right in fields[left_index + 1:]:
            questions.append(
                {
                    "question_id": build_question_id(left, right),
                    "question": f"Does {left} relate to {right} across the population?",
                    "x_field": left,
                    "y_field": right,
                    "kind": "numeric_correlation",
                    "status": "generated",
                }
            )

    return questions[:max_questions]


def build_question_id(left: str, right: str) -> str:
    """Build deterministic question id."""
    clean_left = left.replace(".", "_")
    clean_right = right.replace(".", "_")
    return f"auto::{clean_left}__x__{clean_right}"
