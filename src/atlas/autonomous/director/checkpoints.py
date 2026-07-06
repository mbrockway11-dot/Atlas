
"""Autonomous Director checkpoints."""

from __future__ import annotations

from typing import Any


def build_checkpoint(
    name: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build a Director checkpoint."""
    return {
        "checkpoint": name,
        "success": bool(payload.get("success", True)),
        "summary": payload.get("summary", ""),
        "payload_keys": sorted(payload.keys()),
    }


def checkpoint_status(checkpoints: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize checkpoints."""
    return {
        "success": all(item.get("success") for item in checkpoints),
        "checkpoint_count": len(checkpoints),
        "failed_count": sum(1 for item in checkpoints if not item.get("success")),
        "checkpoints": checkpoints,
    }
