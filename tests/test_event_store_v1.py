from __future__ import annotations

from pathlib import Path

from atlas.investment.events import (
    AtlasEvent,
    EventStore,
    EventType,
)


def event(event_id: str, event_type: EventType = EventType.SIGNAL) -> AtlasEvent:
    return AtlasEvent(
        event_id=event_id,
        event_type=event_type,
        aggregate_type="strategy",
        aggregate_id="alpha-1",
        occurred_at="2026-01-01T00:00:00+00:00",
        source="tests",
        payload={"score": 0.9},
    )


def test_append_assigns_sequence_and_hash_chain(tmp_path: Path) -> None:
    store = EventStore(output_dir=tmp_path)

    first = store.append(event("event-1"))
    second = store.append(event("event-2"))

    assert first.sequence == 1
    assert second.sequence == 2
    assert first.previous_record_hash == ""
    assert second.previous_record_hash == first.record_hash
    assert len(store.all()) == 2


def test_query_by_type_and_aggregate(tmp_path: Path) -> None:
    store = EventStore(output_dir=tmp_path)
    store.append(event("signal-1", EventType.SIGNAL))
    store.append(event("fill-1", EventType.FILL))

    assert len(store.by_type("SIGNAL")) == 1
    assert len(store.by_aggregate("strategy", "alpha-1")) == 2
