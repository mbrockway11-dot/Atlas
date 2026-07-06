
"""Decision comparison utilities."""

from __future__ import annotations

from typing import Any


def compare_decision_paths(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare scored decision paths."""
    if not results:
        return {
            "winner": None,
            "ranking": [],
            "summary": "No decision paths available.",
        }

    ranking = sorted(
        results,
        key=lambda item: item.get("score", {}).get("overall_score", 0.0),
        reverse=True,
    )

    winner = ranking[0]

    return {
        "winner": {
            "choice_id": winner.get("choice", {}).get("choice_id"),
            "label": winner.get("choice", {}).get("label"),
            "overall_score": winner.get("score", {}).get("overall_score"),
            "score_label": winner.get("score", {}).get("label"),
        },
        "ranking": [
            {
                "choice_id": item.get("choice", {}).get("choice_id"),
                "label": item.get("choice", {}).get("label"),
                "overall_score": item.get("score", {}).get("overall_score"),
                "alignment": item.get("score", {}).get("structural_alignment"),
                "growth": item.get("score", {}).get("growth_alignment"),
                "recovery": item.get("score", {}).get("recovery_alignment"),
                "stress": item.get("score", {}).get("stress_load"),
                "score_label": item.get("score", {}).get("label"),
            }
            for item in ranking
        ],
        "summary": build_summary(ranking),
    }


def build_summary(ranking: list[dict[str, Any]]) -> str:
    """Build decision comparison summary."""
    if not ranking:
        return "No decision paths available."

    winner = ranking[0]
    label = winner.get("choice", {}).get("label", "the leading option")
    score = winner.get("score", {}).get("overall_score", 0.0)

    if len(ranking) == 1:
        return (
            f"{label} has an overall structural alignment score of {score:.2f}. "
            "Atlas has no competing path to compare yet."
        )

    runner_up = ranking[1]
    runner_label = runner_up.get("choice", {}).get("label", "the next option")
    runner_score = runner_up.get("score", {}).get("overall_score", 0.0)
    delta = score - runner_score

    return (
        f"{label} currently ranks above {runner_label} by {delta:.2f}. "
        "This does not mean the choice is objectively correct; it means this path better matches the current structural model."
    )
