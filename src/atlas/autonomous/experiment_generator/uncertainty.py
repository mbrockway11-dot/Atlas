
"""Experiment uncertainty scoring."""

from __future__ import annotations

from typing import Any


def score_question_uncertainty(
    question: dict[str, Any],
    memory: dict[str, Any] | None = None,
) -> float:
    """Score uncertainty from lack of prior evidence."""
    if not memory:
        return 1.0

    x_field = str(question.get("x_field", ""))
    y_field = str(question.get("y_field", ""))

    evidence_text = str(memory.get("evidence", {})).lower()
    hits = int(x_field.lower() in evidence_text) + int(y_field.lower() in evidence_text)

    if hits == 0:
        return 1.0
    if hits == 1:
        return 0.65
    return 0.30


def rank_by_uncertainty(
    questions: list[dict[str, Any]],
    memory: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Add uncertainty score and rank."""
    rows = []

    for question in questions:
        rows.append(
            {
                **question,
                "uncertainty": score_question_uncertainty(question, memory),
            }
        )

    return sorted(rows, key=lambda item: item.get("uncertainty", 0.0), reverse=True)
