
"""Research Memory updater."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.memory.memory import (
    add_memory_note,
    remember_evidence,
    remember_experiment,
    remember_hypothesis,
)


def update_memory_from_orchestration(
    memory: dict[str, Any],
    orchestration_report: dict[str, Any],
) -> dict[str, Any]:
    """Update memory from Research Orchestrator output."""
    execution = orchestration_report.get("execution", {}) or {}

    for result in execution.get("results", []) or []:
        memory = remember_experiment(memory, {
            "experiment_id": result.get("task_id"),
            "task_id": result.get("task_id"),
            "goal_id": result.get("goal_id"),
            "question": result.get("question"),
            "status": result.get("status"),
            "summary": result.get("summary"),
            "engines": result.get("engines", []),
        })

        outputs = result.get("outputs", {}) or {}

        discovery = outputs.get("discovery", {}) or {}
        for hypothesis in discovery.get("hypotheses", []) or []:
            memory = remember_hypothesis(memory, hypothesis)

        causality = outputs.get("causality", {}) or {}
        for hypothesis in causality.get("causal_hypotheses", []) or []:
            memory = remember_hypothesis(memory, hypothesis)

    memory = add_memory_note(
        memory,
        orchestration_report.get("summary", "Research orchestration completed."),
        source="research_orchestrator",
    )

    return memory


def update_memory_from_evidence(
    memory: dict[str, Any],
    evidence_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Update memory from evidence records."""
    for record in evidence_records:
        memory = remember_evidence(memory, record)
    return memory
