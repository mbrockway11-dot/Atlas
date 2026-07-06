
"""Experiment novelty scoring."""

from __future__ import annotations

from typing import Any


def score_question_novelty(
    question: dict[str, Any],
    memory: dict[str, Any] | None = None,
) -> float:
    """Score novelty against research memory."""
    if not memory:
        return 1.0

    question_text = str(question.get("question", "")).lower()
    prior = str(memory).lower()

    if question_text and question_text in prior:
        return 0.15

    qid = str(question.get("question_id", "")).lower()
    if qid and qid in prior:
        return 0.10

    return 1.0


def rank_by_novelty(
    questions: list[dict[str, Any]],
    memory: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Add novelty score and rank."""
    rows = []

    for question in questions:
        rows.append(
            {
                **question,
                "novelty": score_question_novelty(question, memory),
            }
        )

    return sorted(rows, key=lambda item: item.get("novelty", 0.0), reverse=True)
