
"""Simulation comparison logic."""

from __future__ import annotations

from typing import Any

from atlas.simulation import build_simulation_report


def compare_simulation_responses(
    left_systems_report: dict[str, Any],
    right_systems_report: dict[str, Any],
    scenarios: list[str],
) -> dict[str, Any]:
    """Compare simulation responses across scenarios."""
    rows = []

    for scenario in scenarios:
        left = build_simulation_report(left_systems_report, scenario=scenario)
        right = build_simulation_report(right_systems_report, scenario=scenario)

        left_action = extract_action(left)
        right_action = extract_action(right)

        rows.append(
            {
                "scenario": scenario,
                "left_action": left_action,
                "right_action": right_action,
                "same_action": left_action == right_action,
                "left_recovery": extract_recovery(left),
                "right_recovery": extract_recovery(right),
                "left_growth": extract_growth(left),
                "right_growth": extract_growth(right),
                "left_simulation": left,
                "right_simulation": right,
            }
        )

    same_count = sum(1 for row in rows if row.get("same_action"))

    return {
        "scenario_count": len(rows),
        "same_action_count": same_count,
        "action_similarity": round(same_count / max(1, len(rows)), 6),
        "rows": rows,
        "summary": build_summary(rows),
    }


def extract_action(simulation: dict[str, Any]) -> str:
    """Extract likely action."""
    sim = simulation.get("simulation", {})
    likely = sim.get("decisions", {}).get("likely_action") or {}
    return str(likely.get("action") or "unresolved")


def extract_recovery(simulation: dict[str, Any]) -> str:
    """Extract recovery mode."""
    sim = simulation.get("simulation", {})
    recovery = sim.get("recovery", {})
    return str(recovery.get("recovery_mode") or "unresolved")


def extract_growth(simulation: dict[str, Any]) -> str:
    """Extract growth vector."""
    growth = simulation.get("growth", {})
    return str(growth.get("current_growth_vector") or "unresolved")


def build_summary(rows: list[dict[str, Any]]) -> str:
    """Build simulation comparison summary."""
    if not rows:
        return "No simulation scenarios were compared."

    same = sum(1 for row in rows if row.get("same_action"))

    if same == len(rows):
        return "Across the selected scenarios, both profiles converged on the same likely actions."

    if same == 0:
        return "Across the selected scenarios, the profiles responded through different action patterns."

    return f"The profiles shared likely actions in {same} of {len(rows)} selected scenarios."
