
"""Autonomous Director report."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.director.director import run_autonomous_director


def build_director_report(
    records: list[dict[str, Any]],
    *,
    goal: str = "general_autonomous_research",
    max_schedule_items: int = 3,
    holdout_ratio: float = 0.20,
    export: bool = True,
) -> dict[str, Any]:
    """Build Director report."""
    return run_autonomous_director(
        records,
        goal=goal,
        max_schedule_items=max_schedule_items,
        holdout_ratio=holdout_ratio,
        export=export,
    )
