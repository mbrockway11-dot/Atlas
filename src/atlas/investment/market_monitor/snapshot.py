"""Snapshot persistence for Atlas G.23 market monitoring."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import ConsolidatedTicker, VenueHealth, VenueTicker
from .errors import MarketDataValidationError


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


def build_snapshot_payload(
    *,
    tickers: Sequence[VenueTicker],
    health: Sequence[VenueHealth],
    consolidated: ConsolidatedTicker,
    previous_record_hash: str = "",
) -> dict[str, Any]:
    if not tickers:
        raise MarketDataValidationError("At least one ticker is required")

    payload = {
        "schema_version": "g23.market_monitor.snapshot.v1",
        "symbol": consolidated.symbol,
        "tickers": [
            {
                **asdict(item),
                "venue": item.venue.value,
            }
            for item in tickers
        ],
        "health": [
            {
                **asdict(item),
                "venue": item.venue.value,
                "state": item.state.value,
            }
            for item in health
        ],
        "consolidated": {
            **asdict(consolidated),
            "best_bid_venue": consolidated.best_bid_venue.value,
            "best_ask_venue": consolidated.best_ask_venue.value,
        },
        "paper_only": True,
        "live_execution": False,
        "credentials_used": False,
        "previous_record_hash": previous_record_hash,
        "record_hash": "",
    }
    payload["record_hash"] = compute_hash(payload)
    return payload


__all__ = [
    "atomic_write_json",
    "build_snapshot_payload",
    "canonical_json",
    "compute_hash",
]
