
"""Research Orchestrator pipeline."""

from __future__ import annotations

from typing import Any

from atlas.research_orchestrator.executor import execute_research_plan
from atlas.research_orchestrator.planner import build_research_plan
from atlas.research_orchestrator.priority import rank_research_tasks
from atlas.research_orchestrator.reports import build_orchestration_report
from atlas.research_orchestrator.scheduler import build_research_schedule


ORCHESTRATOR_VERSION = "1.0.0"


def run_research_orchestration(
    records: list[dict[str, Any]],
    *,
    goals: list[dict[str, Any]] | None = None,
    max_tasks: int = 3,
) -> dict[str, Any]:
    """Run full research orchestration pipeline."""
    plan = build_research_plan(
        goals=goals,
        record_count=len(records),
    )

    ranked_tasks = rank_research_tasks(plan.get("tasks", []))
    plan["tasks"] = ranked_tasks

    schedule = build_research_schedule(
        ranked_tasks,
        max_tasks=max_tasks,
    )

    execution = execute_research_plan(
        {"tasks": ranked_tasks},
        records,
        max_tasks=max_tasks,
    )

    report = build_orchestration_report(
        plan,
        schedule,
        execution,
    )

    return {
        "success": True,
        "version": ORCHESTRATOR_VERSION,
        **report,
    }
