
"""Research planning."""

from __future__ import annotations

from typing import Any


DEFAULT_RESEARCH_GOALS = [
    {
        "goal_id": "validate_dynamic_recovery",
        "question": "Do recurrence and attractor density predict recovery probability?",
        "priority": 0.95,
        "engines": ["discovery", "causality", "knowledge"],
    },
    {
        "goal_id": "test_energy_sensitivity",
        "question": "Is transition energy independently predictive of perturbation sensitivity?",
        "priority": 0.90,
        "engines": ["discovery", "causality"],
    },
    {
        "goal_id": "map_population_dynamics",
        "question": "Which profiles share dynamic basins or response families?",
        "priority": 0.82,
        "engines": ["population_dynamics", "knowledge"],
    },
]


def build_research_plan(
    *,
    goals: list[dict[str, Any]] | None = None,
    record_count: int = 0,
) -> dict[str, Any]:
    """Build research plan."""
    selected_goals = goals or DEFAULT_RESEARCH_GOALS

    tasks = []

    for goal in selected_goals:
        tasks.append(
            {
                "task_id": f"task::{goal.get('goal_id')}",
                "goal_id": goal.get("goal_id"),
                "question": goal.get("question"),
                "priority": float(goal.get("priority") or 0.0),
                "engines": goal.get("engines", []),
                "status": "planned",
                "minimum_records": minimum_records(goal),
                "ready": record_count >= minimum_records(goal),
            }
        )

    tasks.sort(key=lambda item: item["priority"], reverse=True)

    return {
        "success": True,
        "record_count": record_count,
        "goal_count": len(selected_goals),
        "task_count": len(tasks),
        "tasks": tasks,
        "summary": f"Research plan prepared {len(tasks)} task(s) across {record_count} record(s).",
    }


def minimum_records(goal: dict[str, Any]) -> int:
    """Minimum recommended records for goal."""
    engines = set(goal.get("engines", []) or [])

    if "causality" in engines:
        return 30

    if "discovery" in engines:
        return 20

    return 10
