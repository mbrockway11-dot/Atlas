from __future__ import annotations

from pathlib import Path

from atlas.investment.events import (
    AtlasEvent,
    EventBus,
    EventStore,
    EventType,
)


def test_publish_dispatches_to_matching_handler(tmp_path: Path) -> None:
    received: list[str] = []
    bus = EventBus(store=EventStore(output_dir=tmp_path))

    def handler(event: AtlasEvent) -> None:
        received.append(event.event_id)

    bus.subscribe(EventType.FILL, handler)

    result = bus.publish(
        AtlasEvent(
            event_id="fill-1",
            event_type=EventType.FILL,
            aggregate_type="order",
            aggregate_id="order-1",
            occurred_at="2026-01-01T00:00:00+00:00",
            source="tests",
            payload={"quantity": 1},
        )
    )

    assert received == ["fill-1"]
    assert result.handlers_matched == 1
    assert result.handlers_succeeded == 1
    assert result.handlers_failed == 0


def test_non_matching_handler_is_not_called(tmp_path: Path) -> None:
    received: list[str] = []
    bus = EventBus(store=EventStore(output_dir=tmp_path))

    def handler(event: AtlasEvent) -> None:
        received.append(event.event_id)

    bus.subscribe(EventType.FILL, handler)
    result = bus.publish(
        AtlasEvent(
            event_id="signal-1",
            event_type=EventType.SIGNAL,
            aggregate_type="strategy",
            aggregate_id="alpha-1",
            occurred_at="2026-01-01T00:00:00+00:00",
            source="tests",
            payload={},
        )
    )

    assert received == []
    assert result.handlers_matched == 0
