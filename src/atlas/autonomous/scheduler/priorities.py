
"""Scheduler priority utilities."""

from __future__ import annotations

from typing import Any


def score_queue_item(item: dict[str, Any]) -> float:
    """Score queued item."""
    priority = float(item.get("priority") or 0.0)
    ready_bonus = 0.10 if item.get("status") == "queued" else 0.0
    field_bonus = 0.05 if item.get("x_field") and item.get("y_field") else 0.0

    return round(priority + ready_bonus + field_bonus, 6)


def rank_queue_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank queue items."""
    rows = []

    for item in items:
        rows.append(
            {
                **item,
                "schedule_score": score_queue_item(item),
            }
        )

    return sorted(rows, key=lambda row: row.get("schedule_score", 0.0), reverse=True)
