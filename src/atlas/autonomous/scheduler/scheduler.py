
"""Autonomous research scheduler."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.scheduler.priorities import rank_queue_items


def build_schedule(
    queue: dict[str, Any],
    *,
    max_items: int = 10,
) -> dict[str, Any]:
    """Build execution schedule from queue."""
    ranked = rank_queue_items(queue.get("items", []) or [])
    selected = ranked[:max_items]

    scheduled = []

    for order, item in enumerate(selected, start=1):
        scheduled.append(
            {
                **item,
                "order": order,
                "status": "scheduled",
            }
        )

    return {
        "success": True,
        "queued_count": len(queue.get("items", []) or []),
        "scheduled_count": len(scheduled),
        "scheduled_items": scheduled,
        "summary": f"Scheduled {len(scheduled)} item(s) from {len(queue.get('items', []) or [])} queued item(s).",
    }
