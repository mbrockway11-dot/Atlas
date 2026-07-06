
"""Service layer for Research Orchestrator."""

from __future__ import annotations

from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.research_orchestrator import run_research_orchestration
from atlas.services.discovery_service import build_discovery_records


def list_research_profiles() -> list[str]:
    """List saved profiles."""
    return list_saved_profiles()


def build_research_orchestrator_payload(
    profile_keys: list[str] | None = None,
    *,
    limit: int | None = 50,
    force: bool = False,
    max_tasks: int = 3,
    goals: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build service-backed Research Orchestrator payload."""
    records = build_discovery_records(
        profile_keys,
        limit=limit,
        force=force,
    )

    report = run_research_orchestration(
        records,
        goals=goals,
        max_tasks=max_tasks,
    )

    return {
        "success": True,
        "record_count": len(records),
        "profile_keys": [record.get("profile_key") for record in records],
        "orchestration": report,
        "summary": report.get("summary", ""),
        "insights": report.get("insights", []),
    }
