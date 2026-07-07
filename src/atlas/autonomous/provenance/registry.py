
"""Research provenance registry."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


PREFIXES = {
    "DISCOVERY": "DISCOVERY",
    "EVIDENCE": "EVIDENCE",
    "HYPOTHESIS": "HYPOTHESIS",
    "THEORY": "THEORY",
    "PREDICTION": "PREDICTION",
    "CAMPAIGN": "CAMPAIGN",
    "LEARNING": "LEARNING",
    "DIRECTOR": "DIRECTOR",
    "CONFIDENCE": "CONFIDENCE",
    "FALSIFICATION": "FALSIFICATION",
}


def create_registry() -> dict[str, Any]:
    """Create empty append-only provenance registry."""
    return {
        "success": True,
        "counters": {},
        "objects": {},
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }


def next_id(registry: dict[str, Any], object_type: str) -> str:
    """Generate next immutable object id."""
    normalized = object_type.upper()
    prefix = PREFIXES.get(normalized, normalized)

    counters = registry.setdefault("counters", {})
    counters[prefix] = int(counters.get(prefix, 0)) + 1

    registry["updated_at"] = utc_now()
    return f"{prefix}-{counters[prefix]:06d}"


def register_object(
    registry: dict[str, Any],
    *,
    object_type: str,
    payload: dict[str, Any],
    label: str = "",
) -> dict[str, Any]:
    """Register an object immutably."""
    object_id = next_id(registry, object_type)

    registry.setdefault("objects", {})[object_id] = {
        "id": object_id,
        "type": object_type.lower(),
        "label": label or infer_label(payload, object_type),
        "payload": payload,
        "created_at": utc_now(),
    }

    registry["updated_at"] = utc_now()
    return {
        "registry": registry,
        "object_id": object_id,
    }


def infer_label(payload: dict[str, Any], object_type: str) -> str:
    """Infer human-readable object label."""
    return (
        payload.get("label")
        or payload.get("summary")
        or payload.get("question")
        or payload.get("theory_id")
        or payload.get("evidence_id")
        or object_type.lower()
    )


def utc_now() -> str:
    """Return UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()
