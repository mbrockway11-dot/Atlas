
"""Experiment ranking."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.experiment_generator.novelty import score_question_novelty
from atlas.autonomous.experiment_generator.uncertainty import score_question_uncertainty


def rank_experiment_questions(
    questions: list[dict[str, Any]],
    *,
    memory: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Rank generated questions by novelty and uncertainty."""
    rows = []

    for question in questions:
        novelty = score_question_novelty(question, memory)
        uncertainty = score_question_uncertainty(question, memory)
        feasibility = score_feasibility(question)

        rank_score = novelty * 0.40 + uncertainty * 0.35 + feasibility * 0.25

        rows.append(
            {
                **question,
                "novelty": round(novelty, 6),
                "uncertainty": round(uncertainty, 6),
                "feasibility": round(feasibility, 6),
                "rank_score": round(rank_score, 6),
            }
        )

    return sorted(rows, key=lambda item: item.get("rank_score", 0.0), reverse=True)


def score_feasibility(question: dict[str, Any]) -> float:
    """Score whether the question is currently feasible."""
    if question.get("x_field") and question.get("y_field"):
        return 1.0
    return 0.0
