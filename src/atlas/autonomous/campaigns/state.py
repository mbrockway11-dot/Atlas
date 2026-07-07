
"""Campaign state management."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def transition_campaign(
    campaign: dict[str, Any],
    status: str,
    *,
    note: str = "",
) -> dict[str, Any]:
    """Transition campaign status."""
    campaign.setdefault("history", []).append(
        {
            "from": campaign.get("status"),
            "to": status,
            "note": note,
            "timestamp": utc_now(),
        }
    )
    campaign["status"] = status
    campaign["updated_at"] = utc_now()
    return campaign


def add_campaign_cycle(
    campaign: dict[str, Any],
    cycle_report: dict[str, Any],
) -> dict[str, Any]:
    """Add cycle report to campaign."""
    cycles = campaign.setdefault("cycles", [])
    cycles.append(
        {
            "cycle_index": len(cycles) + 1,
            "summary": cycle_report.get("summary", ""),
            "health": cycle_report.get("health", {}),
            "learning_update": ((cycle_report.get("lifecycle", {}) or {}).get("cycle", {}) or {}).get("learning_update", {}),
            "theory": ((cycle_report.get("lifecycle", {}) or {}).get("cycle", {}) or {}).get("theory", {}),
            "prediction": ((cycle_report.get("lifecycle", {}) or {}).get("cycle", {}) or {}).get("prediction", {}),
            "director": cycle_report,
        }
    )
    campaign["updated_at"] = utc_now()
    return campaign


def utc_now() -> str:
    """Return UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()
