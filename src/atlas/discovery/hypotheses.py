
"""Discovery hypothesis builder."""

from __future__ import annotations

from typing import Any


def build_hypotheses(correlation_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build hypotheses from correlation results."""
    hypotheses = []

    for result in correlation_results:
        strength = result.get("strength")

        if strength in {"minimal", "insufficient_sample"}:
            continue

        hypotheses.append(
            {
                "hypothesis_id": f"hypothesis::{result.get('question_id')}",
                "question_id": result.get("question_id"),
                "hypothesis": build_hypothesis_text(result),
                "confidence": hypothesis_confidence(result),
                "strength": strength,
                "direction": result.get("direction"),
                "correlation": result.get("correlation"),
                "sample_size": result.get("sample_size"),
                "evidence": {
                    "x_field": result.get("x_field"),
                    "y_field": result.get("y_field"),
                    "supporting_rows": result.get("supporting_rows", []),
                },
            }
        )

    return sorted(
        hypotheses,
        key=lambda item: item.get("confidence", 0.0),
        reverse=True,
    )


def build_hypothesis_text(result: dict[str, Any]) -> str:
    """Build hypothesis text."""
    direction = result.get("direction")
    strength = result.get("strength")
    question = result.get("question")

    if direction == "positive":
        return f"{question} Preliminary scan suggests a {strength} positive relationship."
    if direction == "negative":
        return f"{question} Preliminary scan suggests a {strength} negative relationship."

    return f"{question} Preliminary scan suggests a {strength} neutral or mixed relationship."


def hypothesis_confidence(result: dict[str, Any]) -> float:
    """Score hypothesis confidence."""
    strength_score = {
        "strong": 0.80,
        "moderate": 0.62,
        "weak": 0.42,
    }.get(result.get("strength"), 0.20)

    sample_size = int(result.get("sample_size") or 0)
    sample_bonus = min(0.15, sample_size / 200)

    return round(min(0.95, strength_score + sample_bonus), 6)
