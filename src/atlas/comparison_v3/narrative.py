
"""Narrative layer for Comparison v3."""

from __future__ import annotations

from typing import Any


def build_comparison_narrative(report: dict[str, Any]) -> dict[str, Any]:
    """Build human-readable comparison narrative."""
    left = report.get("left_profile_key", "Left")
    right = report.get("right_profile_key", "Right")

    themes = report.get("themes", {})
    simulations = report.get("simulation_responses", {})
    evolution = report.get("evolution_patterns", {})

    return {
        "headline": build_headline(left, right, themes, simulations),
        "overview": build_overview(left, right, themes, simulations, evolution),
        "shared_architecture": themes.get("summary", ""),
        "inference_path": report.get("inferences", {}).get("summary", ""),
        "behavioral_response": simulations.get("summary", ""),
        "adaptation_pattern": evolution.get("summary", ""),
        "watch_for": build_watch_for(themes, simulations, evolution),
    }


def build_headline(
    left: str,
    right: str,
    themes: dict[str, Any],
    simulations: dict[str, Any],
) -> str:
    """Build narrative headline."""
    theme_similarity = float(themes.get("similarity") or 0.0)
    action_similarity = float(simulations.get("action_similarity") or 0.0)

    if theme_similarity >= 0.50 and action_similarity >= 0.50:
        return f"{left} and {right} show strong structural and behavioral overlap."

    if theme_similarity >= 0.50:
        return f"{left} and {right} share architecture but may behave differently under pressure."

    if action_similarity >= 0.50:
        return f"{left} and {right} differ architecturally but converge in simulated response."

    return f"{left} and {right} show distinct structural and behavioral patterns."


def build_overview(
    left: str,
    right: str,
    themes: dict[str, Any],
    simulations: dict[str, Any],
    evolution: dict[str, Any],
) -> str:
    """Build overview narrative."""
    return (
        f"Atlas compared {left} and {right} across themes, inference paths, simulation responses, "
        "and evolution patterns. "
        f"Theme similarity is {themes.get('similarity')}; "
        f"simulation action similarity is {simulations.get('action_similarity')}; "
        f"evolution pattern: {evolution.get('summary')}"
    )


def build_watch_for(
    themes: dict[str, Any],
    simulations: dict[str, Any],
    evolution: dict[str, Any],
) -> list[str]:
    """Build watch-for list."""
    bullets: list[str] = []

    if float(themes.get("similarity") or 0.0) < 0.25:
        bullets.append("Low theme overlap may produce different priorities, interpretations, or definitions of success.")

    if float(simulations.get("action_similarity") or 0.0) < 0.50:
        bullets.append("Different simulated action styles may require explicit coordination under pressure.")

    if not evolution.get("same_learning_signal"):
        bullets.append("Different adaptation patterns may cause each profile to grow from the same experience in different directions.")

    if not bullets:
        bullets.append("The comparison is coherent, but real-world context should still be checked before interpretation.")

    return bullets
