
"""Research timeline event models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def create_timeline_event(
    *,
    event_type: str,
    title: str,
    summary: str = "",
    source_id: str = "",
    payload: dict[str, Any] | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Create timeline event."""
    return {
        "event_id": build_event_id(event_type, title, timestamp or utc_now()),
        "event_type": event_type,
        "title": title,
        "summary": summary,
        "source_id": source_id,
        "payload": payload or {},
        "timestamp": timestamp or utc_now(),
    }


def build_event_id(event_type: str, title: str, timestamp: str) -> str:
    """Build deterministic-ish event id."""
    clean_title = "".join(ch.lower() if ch.isalnum() else "_" for ch in title)
    clean_title = "_".join(part for part in clean_title.split("_") if part)[:48]
    clean_time = timestamp.replace("-", "").replace(":", "").replace(".", "").replace("+", "_")
    return f"event::{event_type.lower()}::{clean_title}::{clean_time}"


def utc_now() -> str:
    """Return UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()
