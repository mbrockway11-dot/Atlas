
"""Autonomous learning loop."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.evidence import (
    build_evidence_from_causality,
    build_evidence_from_discovery,
    create_evidence_registry,
    register_many,
)
from atlas.autonomous.experiment_generator import build_experiment_plan
from atlas.autonomous.falsification import build_falsification_report
from atlas.autonomous.learning.updater import build_learning_update
from atlas.autonomous.memory import (
    create_research_memory,
    update_memory_from_evidence,
)
from atlas.autonomous.prediction import build_prediction_challenge_report
from atlas.autonomous.scheduler import build_autonomous_scheduler_report
from atlas.autonomous.theory import build_theory_report
from atlas.causality import build_causal_hypothesis_report
from atlas.discovery import build_discovery_report


def run_autonomous_learning_cycle(
    records: list[dict[str, Any]],
    *,
    memory: dict[str, Any] | None = None,
    max_schedule_items: int = 3,
    holdout_ratio: float = 0.20,
) -> dict[str, Any]:
    """Run one full autonomous learning cycle."""
    working_memory = memory or create_research_memory()

    discovery = build_discovery_report(records)
    causality = build_causal_hypothesis_report(records)

    evidence_records = (
        build_evidence_from_discovery(discovery)
        + build_evidence_from_causality(causality)
    )

    evidence_registry = create_evidence_registry()
    evidence_registry = register_many(evidence_registry, evidence_records)

    working_memory = update_memory_from_evidence(
        working_memory,
        evidence_records,
    )

    experiment_plan = build_experiment_plan(
        memory=working_memory,
        top_n=10,
    )

    scheduler_report = build_autonomous_scheduler_report(
        records,
        memory=working_memory,
        max_schedule_items=max_schedule_items,
        execute=True,
    )

    hypotheses = (
        discovery.get("hypotheses", [])
        + causality.get("causal_hypotheses", [])
    )

    theory_report = build_theory_report(
        evidence_records,
        hypotheses=hypotheses,
    )

    falsification_report = build_falsification_report(
        theory_report.get("theories", []),
        evidence_records,
    )

    prediction_report = build_prediction_challenge_report(
        records,
        holdout_ratio=holdout_ratio,
    )

    learning_update = build_learning_update(
        evidence=evidence_registry,
        memory=working_memory,
        experiment_plan=experiment_plan,
        scheduler_report=scheduler_report,
        theory_report=theory_report,
        falsification_report=falsification_report,
        prediction_report=prediction_report,
    )

    return {
        "success": True,
        "record_count": len(records),
        "discovery": discovery,
        "causality": causality,
        "evidence_registry": evidence_registry,
        "memory": working_memory,
        "experiment_plan": experiment_plan,
        "scheduler": scheduler_report,
        "theory": theory_report,
        "falsification": falsification_report,
        "prediction": prediction_report,
        "learning_update": learning_update,
        "summary": learning_update.get("summary", ""),
    }
