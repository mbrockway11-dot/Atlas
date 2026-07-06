
"""Service layer for Autonomous Lab."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.learning import build_autonomous_learning_report
from atlas.autonomous.director import build_director_report
from atlas.autonomous.memory import ensure_research_memory, persist_research_memory
from atlas.library.profile_library import list_saved_profiles
from atlas.services.discovery_service import build_discovery_records


def list_autonomous_profiles() -> list[str]:
    """List saved profiles."""
    return list_saved_profiles()


def build_autonomous_lab_payload(
    profile_keys: list[str] | None = None,
    *,
    limit: int | None = 50,
    force: bool = False,
    max_schedule_items: int = 3,
    holdout_ratio: float = 0.20,
) -> dict[str, Any]:
    """Build service-backed Autonomous Lab payload."""
    records = build_discovery_records(
        profile_keys,
        limit=limit,
        force=force,
    )

    memory = ensure_research_memory()

    report = build_autonomous_learning_report(
        records,
        memory=memory,
        max_schedule_items=max_schedule_items,
        holdout_ratio=holdout_ratio,
    )

    memory_result = persist_research_memory(report.get("memory", memory))

    return {
        "success": True,
        "record_count": len(records),
        "profile_keys": [record.get("profile_key") for record in records],
        "memory_persistence": memory_result,
        "autonomous": report,
        "summary": report.get("summary", ""),
        "learning_update": report.get("learning_update", {}),
        "theory": report.get("theory", {}),
        "prediction": report.get("prediction", {}),
        "falsification": report.get("falsification", {}),
    }



def build_autonomous_director_payload(
    profile_keys: list[str] | None = None,
    *,
    limit: int | None = 50,
    force: bool = False,
    goal: str = "general_autonomous_research",
    max_schedule_items: int = 3,
    holdout_ratio: float = 0.20,
    export: bool = True,
) -> dict[str, Any]:
    """Build service-backed Autonomous Director payload."""
    records = build_discovery_records(
        profile_keys,
        limit=limit,
        force=force,
    )

    report = build_director_report(
        records,
        goal=goal,
        max_schedule_items=max_schedule_items,
        holdout_ratio=holdout_ratio,
        export=export,
    )

    cycle = report.get("lifecycle", {}).get("cycle", {})

    return {
        "success": True,
        "record_count": len(records),
        "profile_keys": [record.get("profile_key") for record in records],
        "director": report,
        "autonomous": cycle,
        "summary": report.get("summary", ""),
        "health": report.get("health", {}),
        "checkpoints": report.get("checkpoints", {}),
        "learning_update": cycle.get("learning_update", {}),
        "theory": cycle.get("theory", {}),
        "prediction": cycle.get("prediction", {}),
        "falsification": cycle.get("falsification", {}),
    }
