"""Append-only event-store persistence for Atlas G.22."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from .errors import EventIntegrityError


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_hash(record: Mapping[str, Any]) -> str:
    material = dict(record)
    material.pop("record_hash", None)
    return hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(payload))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EventIntegrityError(
                f"Malformed event record at {path}:{line_number}"
            ) from exc
        if not isinstance(record, dict):
            raise EventIntegrityError(
                f"Event record at {path}:{line_number} is not an object"
            )
        records.append(record)
    return records


def validate_hash_chain(records: Sequence[Mapping[str, Any]]) -> None:
    previous = ""
    expected_sequence = 1
    seen_ids: set[str] = set()

    for index, record in enumerate(records):
        event_id = str(record.get("event_id", ""))
        if not event_id:
            raise EventIntegrityError(f"Missing event_id at record {index}")
        if event_id in seen_ids:
            raise EventIntegrityError(f"Duplicate event_id in store: {event_id}")
        seen_ids.add(event_id)

        if int(record.get("sequence", 0)) != expected_sequence:
            raise EventIntegrityError(
                f"Event sequence mismatch at record {index}"
            )
        if record.get("previous_record_hash", "") != previous:
            raise EventIntegrityError(
                f"Event hash-chain mismatch at record {index}"
            )

        expected_hash = compute_hash(record)
        if record.get("record_hash") != expected_hash:
            raise EventIntegrityError(
                f"Event record hash mismatch at record {index}"
            )

        previous = expected_hash
        expected_sequence += 1


__all__ = [
    "append_jsonl",
    "atomic_write_json",
    "canonical_json",
    "compute_hash",
    "read_jsonl",
    "validate_hash_chain",
]
