
"""Comparison v3 report builder."""

from __future__ import annotations

from typing import Any

from atlas.comparison_v3.evolution import compare_evolution_patterns
from atlas.comparison_v3.extractors import extract_profile_summary, extract_systems_report
from atlas.comparison_v3.inference import compare_inferences
from atlas.comparison_v3.narrative import build_comparison_narrative
from atlas.comparison_v3.simulation import compare_simulation_responses
from atlas.comparison_v3.themes import compare_themes


COMPARISON_V3_VERSION = "1.0"


def build_comparison_v3_report(
    left_profile_key: str,
    left_payload: dict[str, Any],
    right_profile_key: str,
    right_payload: dict[str, Any],
    *,
    scenarios: list[str] | None = None,
) -> dict[str, Any]:
    """Build Comparison v3 report."""
    selected_scenarios = scenarios or [
        "public_launch",
        "deep_build",
        "creative_pressure",
    ]

    left_systems = extract_systems_report(left_payload)
    right_systems = extract_systems_report(right_payload)

    themes = compare_themes(left_payload, right_payload)
    inferences = compare_inferences(left_payload, right_payload)

    simulation_responses = compare_simulation_responses(
        left_systems,
        right_systems,
        selected_scenarios,
    )

    evolution_patterns = compare_evolution_patterns(
        left_profile_key,
        right_profile_key,
        simulation_responses,
    )

    report = {
        "success": True,
        "version": COMPARISON_V3_VERSION,
        "left_profile_key": left_profile_key,
        "right_profile_key": right_profile_key,
        "scenarios": selected_scenarios,
        "left_summary": extract_profile_summary(left_payload),
        "right_summary": extract_profile_summary(right_payload),
        "themes": themes,
        "inferences": inferences,
        "simulation_responses": simulation_responses,
        "evolution_patterns": evolution_patterns,
    }

    report["narrative"] = build_comparison_narrative(report)

    return report
