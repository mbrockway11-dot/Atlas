"""Deterministic event replay for Atlas G.22."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, Mapping

from .contracts import EventReplayResult


ReplayHandler = Callable[[Mapping[str, Any]], None]


def replay_events(
    events: Iterable[Mapping[str, Any]],
    handler: ReplayHandler,
) -> EventReplayResult:
    count = 0
    first_event_id: str | None = None
    last_event_id: str | None = None
    final_offset = 0

    for event in events:
        event_id = str(event.get("event_id", ""))
        if first_event_id is None:
            first_event_id = event_id
        handler(event)
        last_event_id = event_id
        final_offset = int(event.get("sequence", count + 1))
        count += 1

    return EventReplayResult(
        events_replayed=count,
        first_event_id=first_event_id,
        last_event_id=last_event_id,
        final_offset=final_offset,
        paper_only=True,
        live_execution=False,
    )


__all__ = ["ReplayHandler", "replay_events"]
