
"""Evolution comparison logic."""

from __future__ import annotations

from typing import Any

from atlas.evolution import build_evolution_report


def compare_evolution_patterns(
    left_profile_key: str,
    right_profile_key: str,
    simulation_comparison: dict[str, Any],
) -> dict[str, Any]:
    """Compare evolution reports generated from paired simulations."""
    rows = simulation_comparison.get("rows", [])

    left_sims = [row.get("left_simulation", {}) for row in rows]
    right_sims = [row.get("right_simulation", {}) for row in rows]

    left = build_evolution_report(left_profile_key, left_sims)
    right = build_evolution_report(right_profile_key, right_sims)

    left_learning = left.get("learning", {})
    right_learning = right.get("learning", {})

    return {
        "left": left,
        "right": right,
        "same_learning_signal": left_learning.get("learning_signal") == right_learning.get("learning_signal"),
        "same_dominant_action": left_learning.get("dominant_action") == right_learning.get("dominant_action"),
        "left_learning_signal": left_learning.get("learning_signal"),
        "right_learning_signal": right_learning.get("learning_signal"),
        "left_dominant_action": left_learning.get("dominant_action"),
        "right_dominant_action": right_learning.get("dominant_action"),
        "summary": build_summary(left_learning, right_learning),
    }


def build_summary(left: dict[str, Any], right: dict[str, Any]) -> str:
    """Build evolution comparison summary."""
    if left.get("learning_signal") == right.get("learning_signal"):
        return (
            "The profiles show similar learning reinforcement across the selected experience sequence: "
            f"{left.get('learning_signal')}."
        )

    return (
        "The profiles adapt differently across the selected experience sequence. "
        f"Left trends toward {left.get('learning_signal')}; right trends toward {right.get('learning_signal')}."
    )
