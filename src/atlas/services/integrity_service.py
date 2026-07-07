
"""Service layer for Research Integrity Lab."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.director import build_director_report
from atlas.autonomous.export import build_autonomous_export_report
from atlas.library.profile_library import list_saved_profiles
from atlas.services.discovery_service import build_discovery_records


def list_integrity_profiles() -> list[str]:
    """List saved profiles."""
    return list_saved_profiles()


def build_research_integrity_payload(
    profile_keys: list[str] | None = None,
    *,
    limit: int | None = 50,
    force: bool = False,
    goal: str = "research_integrity_audit",
    max_schedule_items: int = 2,
    holdout_ratio: float = 0.20,
    export: bool = True,
) -> dict[str, Any]:
    """Build Research Integrity Lab payload."""
    records = build_discovery_records(
        profile_keys,
        limit=limit,
        force=force,
    )

    director = build_director_report(
        records,
        goal=goal,
        max_schedule_items=max_schedule_items,
        holdout_ratio=holdout_ratio,
        export=export,
    )

    cycle = director.get("lifecycle", {}).get("cycle", {}) or {}
    export_report = build_autonomous_export_report(cycle) if export else None

    return {
        "success": True,
        "record_count": len(records),
        "profile_keys": [record.get("profile_key") for record in records],
        "director": director,
        "cycle": cycle,
        "health": director.get("health", {}),
        "scientific_confidence": director.get("scientific_confidence", {}),
        "provenance": director.get("provenance", {}),
        "timeline": director.get("timeline", {}),
        "checkpoints": director.get("checkpoints", {}),
        "export": export_report,
        "summary": build_summary(director),
    }


def build_summary(director: dict[str, Any]) -> str:
    """Build integrity summary."""
    health = director.get("health", {}) or {}
    confidence = director.get("scientific_confidence", {}) or {}
    provenance = director.get("provenance", {}) or {}
    timeline = director.get("timeline", {}) or {}

    return (
        "Research Integrity audit completed. "
        f"Health: {'healthy' if health.get('healthy') else 'warnings'}. "
        f"Scientific confidence: {confidence.get('scientific_confidence')} "
        f"({confidence.get('confidence_label')}). "
        f"Provenance: {provenance.get('summary', 'n/a')} "
        f"Timeline: {timeline.get('text_summary', 'n/a')}"
    )
