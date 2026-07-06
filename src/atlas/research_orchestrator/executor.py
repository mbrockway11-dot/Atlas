
"""Research executor."""

from __future__ import annotations

from typing import Any

from atlas.causality import build_causal_hypothesis_report
from atlas.discovery import build_discovery_report
from atlas.knowledge import build_knowledge_graph_from_discovery


def execute_research_task(
    task: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Execute one research task."""
    engines = set(task.get("engines", []) or {})
    outputs: dict[str, Any] = {}

    if not task.get("ready"):
        return {
            "success": False,
            "task_id": task.get("task_id"),
            "status": "skipped",
            "reason": "insufficient_records",
            "minimum_records": task.get("minimum_records"),
            "record_count": len(records),
        }

    if "discovery" in engines:
        outputs["discovery"] = build_discovery_report(records)

    if "causality" in engines:
        outputs["causality"] = build_causal_hypothesis_report(records)

    if "knowledge" in engines:
        discovery = outputs.get("discovery") or build_discovery_report(records)
        outputs["knowledge"] = build_knowledge_graph_from_discovery(discovery)

    return {
        "success": True,
        "task_id": task.get("task_id"),
        "goal_id": task.get("goal_id"),
        "question": task.get("question"),
        "status": "completed",
        "engines": sorted(engines),
        "outputs": outputs,
        "summary": build_execution_summary(task, outputs),
    }


def execute_research_plan(
    plan: dict[str, Any],
    records: list[dict[str, Any]],
    *,
    max_tasks: int | None = None,
) -> dict[str, Any]:
    """Execute research plan."""
    tasks = plan.get("tasks", []) or []

    if max_tasks is not None:
        tasks = tasks[:max_tasks]

    results = [execute_research_task(task, records) for task in tasks]

    return {
        "success": True,
        "task_count": len(tasks),
        "completed_count": sum(1 for item in results if item.get("success")),
        "skipped_count": sum(1 for item in results if not item.get("success")),
        "results": results,
    }


def build_execution_summary(task: dict[str, Any], outputs: dict[str, Any]) -> str:
    """Build execution summary."""
    return (
        f"Executed {task.get('task_id')} using "
        f"{', '.join(sorted(outputs.keys())) or 'no engines'}."
    )
