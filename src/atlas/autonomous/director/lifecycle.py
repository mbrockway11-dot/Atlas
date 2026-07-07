
"""Autonomous Director lifecycle."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.export import build_autonomous_export_report
from atlas.autonomous.learning import build_autonomous_learning_report
from atlas.autonomous.confidence import build_scientific_confidence_report
from atlas.autonomous.memory import ensure_research_memory, persist_research_memory
from atlas.autonomous.provenance import build_provenance_report
from atlas.autonomous.timeline import build_research_timeline_report


def run_director_lifecycle(
    records: list[dict[str, Any]],
    *,
    max_schedule_items: int = 3,
    holdout_ratio: float = 0.20,
    export: bool = True,
) -> dict[str, Any]:
    """Run one Director lifecycle."""
    memory = ensure_research_memory()

    cycle = build_autonomous_learning_report(
        records,
        memory=memory,
        max_schedule_items=max_schedule_items,
        holdout_ratio=holdout_ratio,
    )

    confidence = build_scientific_confidence_report(cycle)
    cycle["scientific_confidence"] = confidence

    provenance = build_provenance_report(cycle)
    cycle["provenance"] = provenance

    timeline_source = {
        "success": True,
        "goal": "director_lifecycle",
        "summary": cycle.get("summary", ""),
        "health": {"success": True, "healthy": True, "warning_count": 0, "warnings": []},
        "lifecycle": {"cycle": cycle},
    }
    timeline = build_research_timeline_report(timeline_source, export=False)
    cycle["timeline"] = timeline

    memory_result = persist_research_memory(cycle.get("memory", memory))

    export_result = None
    if export:
        export_result = build_autonomous_export_report(cycle)

    return {
        "success": True,
        "record_count": len(records),
        "cycle": cycle,
        "scientific_confidence": confidence,
        "provenance": provenance,
        "timeline": timeline,
        "memory_persistence": memory_result,
        "export": export_result,
        "summary": cycle.get("summary", ""),
    }
