
"""Research timeline summaries."""

from __future__ import annotations

from typing import Any


def summarize_timeline(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize timeline."""
    counts: dict[str, int] = {}

    for event in events:
        event_type = str(event.get("event_type", "unknown"))
        counts[event_type] = counts.get(event_type, 0) + 1

    return {
        "event_count": len(events),
        "event_type_counts": counts,
        "first_event": events[0].get("timestamp") if events else None,
        "last_event": events[-1].get("timestamp") if events else None,
    }
