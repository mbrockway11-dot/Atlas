
"""Autonomous Learning report."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.learning.loop import run_autonomous_learning_cycle


LEARNING_VERSION = "1.0.0"


def build_autonomous_learning_report(
    records: list[dict[str, Any]],
    *,
    memory: dict[str, Any] | None = None,
    max_schedule_items: int = 3,
    holdout_ratio: float = 0.20,
) -> dict[str, Any]:
    """Build autonomous learning report."""
    cycle = run_autonomous_learning_cycle(
        records,
        memory=memory,
        max_schedule_items=max_schedule_items,
        holdout_ratio=holdout_ratio,
    )

    return {
        "success": True,
        "version": LEARNING_VERSION,
        **cycle,
    }
