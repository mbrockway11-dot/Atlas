
"""Research scheduler."""

from __future__ import annotations

from typing import Any


def build_research_schedule(
    ranked_tasks: list[dict[str, Any]],
    *,
    max_tasks: int = 5,
) -> dict[str, Any]:
    """Build simple execution schedule."""
    scheduled = []

    for index, task in enumerate(ranked_tasks[:max_tasks], start=1):
        scheduled.append(
            {
                "order": index,
                "task_id": task.get("task_id"),
                "goal_id": task.get("goal_id"),
                "question": task.get("question"),
                "rank_score": task.get("rank_score"),
                "ready": task.get("ready"),
            }
        )

    return {
        "success": True,
        "scheduled_count": len(scheduled),
        "scheduled_tasks": scheduled,
    }
