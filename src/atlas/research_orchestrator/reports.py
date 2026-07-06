
"""Research Orchestrator reports."""

from __future__ import annotations

from typing import Any


def build_orchestration_report(
    plan: dict[str, Any],
    schedule: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, Any]:
    """Build final orchestration report."""
    return {
        "success": True,
        "plan": plan,
        "schedule": schedule,
        "execution": execution,
        "summary": build_summary(plan, execution),
        "insights": extract_research_insights(execution),
    }


def build_summary(plan: dict[str, Any], execution: dict[str, Any]) -> str:
    """Build summary."""
    return (
        f"Research Orchestrator planned {plan.get('task_count', 0)} task(s), "
        f"executed {execution.get('completed_count', 0)}, "
        f"and skipped {execution.get('skipped_count', 0)}."
    )


def extract_research_insights(execution: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract compact insights from execution outputs."""
    insights = []

    for result in execution.get("results", []) or []:
        outputs = result.get("outputs", {}) or {}

        discovery = outputs.get("discovery", {})
        if discovery:
            insights.append(
                {
                    "task_id": result.get("task_id"),
                    "engine": "discovery",
                    "summary": discovery.get("summary"),
                    "hypothesis_count": discovery.get("hypothesis_count"),
                }
            )

        causality = outputs.get("causality", {})
        if causality:
            insights.append(
                {
                    "task_id": result.get("task_id"),
                    "engine": "causality",
                    "summary": causality.get("summary"),
                    "candidate_count": causality.get("candidate_count"),
                }
            )

        knowledge = outputs.get("knowledge", {})
        if knowledge:
            insights.append(
                {
                    "task_id": result.get("task_id"),
                    "engine": "knowledge",
                    "summary": knowledge.get("summary"),
                }
            )

    return insights
