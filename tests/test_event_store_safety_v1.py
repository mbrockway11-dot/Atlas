from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.investment.events import (
    AtlasEvent,
    DuplicateEventError,
    EventIntegrityError,
    EventStore,
    EventType,
    EventValidationError,
)


def safe_event(event_id: str = "event-1") -> AtlasEvent:
    return AtlasEvent(
        event_id=event_id,
        event_type=EventType.EXECUTION_INTENT,
        aggregate_type="intent",
        aggregate_id="intent-1",
        occurred_at="2026-01-01T00:00:00+00:00",
        source="tests",
        payload={"action": "NO_ACTION"},
    )


def test_duplicate_event_is_rejected(tmp_path: Path) -> None:
    store = EventStore(output_dir=tmp_path)
    store.append(safe_event())

    with pytest.raises(DuplicateEventError):
        store.append(safe_event())


def test_live_event_is_rejected(tmp_path: Path) -> None:
    store = EventStore(output_dir=tmp_path)

    with pytest.raises(EventValidationError, match="paper-only"):
        store.append(
            AtlasEvent(
                event_id="live-1",
                event_type=EventType.EXECUTION_INTENT,
                aggregate_type="intent",
                aggregate_id="intent-1",
                occurred_at="2026-01-01T00:00:00+00:00",
                source="tests",
                payload={},
                paper_only=False,
                live_execution=True,
            )
        )


def test_credentials_used_is_rejected(tmp_path: Path) -> None:
    store = EventStore(output_dir=tmp_path)

    with pytest.raises(EventValidationError, match="credentials_used"):
        store.append(
            AtlasEvent(
                event_id="credentials-1",
                event_type=EventType.SYSTEM,
                aggregate_type="system",
                aggregate_id="atlas",
                occurred_at="2026-01-01T00:00:00+00:00",
                source="tests",
                payload={},
                credentials_used=True,
            )
        )


def test_tampered_history_is_detected(tmp_path: Path) -> None:
    store = EventStore(output_dir=tmp_path)
    store.append(safe_event())

    path = tmp_path / "events.jsonl"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["payload"]["action"] = "BUY"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(EventIntegrityError, match="hash"):
        store.all()
