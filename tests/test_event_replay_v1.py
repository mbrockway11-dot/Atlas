from __future__ import annotations

from pathlib import Path

from atlas.investment.events import (
    AtlasEvent,
    EventStore,
    EventType,
    replay_events,
)


def test_replay_is_deterministic(tmp_path: Path) -> None:
    store = EventStore(output_dir=tmp_path)
    for index in range(3):
        store.append(
            AtlasEvent(
                event_id=f"event-{index + 1}",
                event_type=EventType.SYSTEM,
                aggregate_type="system",
                aggregate_id="atlas",
                occurred_at=f"2026-01-01T00:00:0{index}+00:00",
                source="tests",
                payload={"index": index},
            )
        )

    first: list[str] = []
    second: list[str] = []

    first_result = replay_events(
        store.all(),
        lambda event: first.append(event["event_id"]),
    )
    second_result = replay_events(
        store.all(),
        lambda event: second.append(event["event_id"]),
    )

    assert first == second == ["event-1", "event-2", "event-3"]
    assert first_result == second_result
    assert first_result.events_replayed == 3
