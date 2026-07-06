
"""Research priority scoring."""

from __future__ import annotations

from typing import Any


def rank_research_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank research tasks by priority, readiness, and engine value."""
    rows = []

    for task in tasks:
        rows.append(
            {
                **task,
                "rank_score": score_task(task),
            }
        )

    return sorted(rows, key=lambda item: item.get("rank_score", 0.0), reverse=True)


def score_task(task: dict[str, Any]) -> float:
    """Score research task."""
    priority = float(task.get("priority") or 0.0)
    ready_bonus = 0.15 if task.get("ready") else -0.20
    engine_bonus = min(0.20, len(task.get("engines", []) or []) * 0.05)

    return round(max(0.0, priority + ready_bonus + engine_bonus), 6)
