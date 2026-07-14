"""Persistence helpers for Atlas G.21 portfolio ledger."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from .errors import LedgerIntegrityError


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
            raise LedgerIntegrityError(
                f"Malformed JSONL at {path}:{line_number}"
            ) from exc
        if not isinstance(record, dict):
            raise LedgerIntegrityError(
                f"Ledger record at {path}:{line_number} is not an object"
            )
        records.append(record)
    return records


def validate_hash_chain(
    records: Sequence[Mapping[str, Any]],
    *,
    previous_field: str = "previous_record_hash",
    hash_field: str = "record_hash",
) -> None:
    previous = ""
    for index, record in enumerate(records):
        if record.get(previous_field, "") != previous:
            raise LedgerIntegrityError(
                f"Hash chain mismatch at record {index}"
            )
        expected = compute_hash(record)
        if record.get(hash_field) != expected:
            raise LedgerIntegrityError(
                f"Record hash mismatch at record {index}"
            )
        previous = expected


__all__ = [
    "append_jsonl",
    "atomic_write_json",
    "canonical_json",
    "compute_hash",
    "read_jsonl",
    "validate_hash_chain",
]
