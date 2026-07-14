"""Canonical append-only event store for Atlas G.22."""

from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import Path
from typing import Iterable

from .contracts import AtlasEvent, EventCursor
from .errors import DuplicateEventError, EventValidationError
from .persistence import (
    append_jsonl,
    atomic_write_json,
    compute_hash,
    read_jsonl,
    validate_hash_chain,
)


class EventStore:
    def __init__(self, *, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.events_path = output_dir / "events.jsonl"
        self.cursor_path = output_dir / "cursor.json"
        self.latest_path = output_dir / "latest_event.json"

    def append(self, event: AtlasEvent) -> AtlasEvent:
        self._validate_event(event)

        records = read_jsonl(self.events_path)
        if records:
            validate_hash_chain(records)

        if any(record.get("event_id") == event.event_id for record in records):
            raise DuplicateEventError(f"Duplicate event_id: {event.event_id}")

        sequence = len(records) + 1
        previous_hash = records[-1]["record_hash"] if records else ""
        stored = replace(
            event,
            sequence=sequence,
            previous_record_hash=previous_hash,
            record_hash="",
        )
        payload = asdict(stored)
        payload["event_type"] = stored.event_type.value
        payload["record_hash"] = compute_hash(payload)
        stored = replace(stored, record_hash=payload["record_hash"])

        append_jsonl(self.events_path, payload)
        atomic_write_json(self.latest_path, payload)
        atomic_write_json(
            self.cursor_path,
            asdict(
                EventCursor(
                    offset=sequence,
                    last_event_id=stored.event_id,
                    last_record_hash=stored.record_hash,
                )
            ),
        )
        return stored

    def append_many(self, events: Iterable[AtlasEvent]) -> tuple[AtlasEvent, ...]:
        return tuple(self.append(event) for event in events)

    def all(self) -> list[dict]:
        records = read_jsonl(self.events_path)
        if records:
            validate_hash_chain(records)
        return records

    def read_from(self, offset: int = 0) -> list[dict]:
        if offset < 0:
            raise EventValidationError("offset cannot be negative")
        return self.all()[offset:]

    def by_type(self, event_type: str) -> list[dict]:
        normalized = event_type.strip().upper()
        return [
            record
            for record in self.all()
            if str(record.get("event_type", "")).upper() == normalized
        ]

    def by_aggregate(self, aggregate_type: str, aggregate_id: str) -> list[dict]:
        return [
            record
            for record in self.all()
            if record.get("aggregate_type") == aggregate_type
            and record.get("aggregate_id") == aggregate_id
        ]

    @staticmethod
    def _validate_event(event: AtlasEvent) -> None:
        if not event.event_id.strip():
            raise EventValidationError("event_id is required")
        if not event.aggregate_type.strip():
            raise EventValidationError("aggregate_type is required")
        if not event.aggregate_id.strip():
            raise EventValidationError("aggregate_id is required")
        if not event.source.strip():
            raise EventValidationError("source is required")
        if not event.occurred_at.strip():
            raise EventValidationError("occurred_at is required")
        if not isinstance(event.payload, dict):
            raise EventValidationError("payload must be a dictionary")
        if not event.paper_only or event.live_execution:
            raise EventValidationError("Event violates paper-only boundary")
        if event.credentials_used:
            raise EventValidationError("credentials_used must be false")


__all__ = ["EventStore"]
