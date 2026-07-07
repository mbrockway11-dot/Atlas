
"""Autonomous Research Campaign models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


CAMPAIGN_VERSION = "1.0.0"


def create_campaign(
    *,
    campaign_id: str,
    goal: str,
    description: str = "",
    max_cycles: int = 5,
    confidence_target: float = 0.80,
) -> dict[str, Any]:
    """Create research campaign."""
    return {
        "success": True,
        "version": CAMPAIGN_VERSION,
        "campaign_id": campaign_id,
        "goal": goal,
        "description": description,
        "status": "created",
        "max_cycles": int(max_cycles),
        "confidence_target": float(confidence_target),
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "cycles": [],
        "current_confidence": 0.0,
        "summary": "",
    }


def utc_now() -> str:
    """Return UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()
