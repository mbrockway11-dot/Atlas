
"""Experiment planner."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.experiment_generator.generator import generate_experiment_questions
from atlas.autonomous.experiment_generator.ranking import rank_experiment_questions


def build_experiment_plan(
    *,
    variables: list[str] | None = None,
    memory: dict[str, Any] | None = None,
    max_questions: int = 25,
    top_n: int = 10,
) -> dict[str, Any]:
    """Build autonomous experiment plan."""
    generated = generate_experiment_questions(
        variables=variables,
        max_questions=max_questions,
    )

    ranked = rank_experiment_questions(
        generated,
        memory=memory,
    )

    selected = ranked[:top_n]

    return {
        "success": True,
        "generated_count": len(generated),
        "selected_count": len(selected),
        "questions": generated,
        "ranked_questions": ranked,
        "selected_questions": selected,
        "summary": f"Generated {len(generated)} experiment question(s) and selected {len(selected)} for investigation.",
    }
