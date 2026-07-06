
"""Autonomous Scheduler report."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.experiment_generator import build_experiment_plan
from atlas.autonomous.scheduler.executor import execute_scheduled_questions
from atlas.autonomous.scheduler.queue import create_research_queue, enqueue_many
from atlas.autonomous.scheduler.scheduler import build_schedule


SCHEDULER_VERSION = "1.0.0"


def build_autonomous_scheduler_report(
    records: list[dict[str, Any]],
    *,
    memory: dict[str, Any] | None = None,
    max_questions: int = 25,
    top_n: int = 10,
    max_schedule_items: int = 5,
    execute: bool = True,
) -> dict[str, Any]:
    """Build full autonomous scheduler report."""
    experiment_plan = build_experiment_plan(
        memory=memory,
        max_questions=max_questions,
        top_n=top_n,
    )

    queue = create_research_queue()
    queue = enqueue_many(queue, experiment_plan.get("selected_questions", []))

    schedule = build_schedule(queue, max_items=max_schedule_items)

    execution = None
    if execute:
        execution = execute_scheduled_questions(records, schedule)

    return {
        "success": True,
        "version": SCHEDULER_VERSION,
        "record_count": len(records),
        "experiment_plan": experiment_plan,
        "queue": queue,
        "schedule": schedule,
        "execution": execution,
        "summary": build_summary(experiment_plan, schedule, execution),
    }


def build_summary(
    experiment_plan: dict[str, Any],
    schedule: dict[str, Any],
    execution: dict[str, Any] | None,
) -> str:
    """Build summary."""
    text = (
        f"Autonomous Scheduler generated {experiment_plan.get('generated_count', 0)} question(s), "
        f"selected {experiment_plan.get('selected_count', 0)}, "
        f"and scheduled {schedule.get('scheduled_count', 0)}."
    )

    if execution:
        text += f" {execution.get('summary', '')}"

    return text
