"""Regression tests for Atlas Architecture Consolidation v1."""

from __future__ import annotations

from atlas.investment.research_orchestrator.safety import (
    resolve_registered_command,
)
from atlas.investment.research_scheduler import (
    JOB_MAP,
    JOBS,
    topological_order,
)


def test_canonical_registry_has_unique_job_ids():
    job_ids = [job.job_id for job in JOBS]

    assert len(job_ids) == len(set(job_ids))
    assert set(job_ids) == set(JOB_MAP)


def test_research_evidence_precedes_variant_governance():
    ordered = topological_order()

    assert ordered.index(
        "research_experiment_execution"
    ) < ordered.index(
        "research_evidence_accumulator"
    )

    assert ordered.index(
        "research_evidence_accumulator"
    ) < ordered.index(
        "validated_variant_registry"
    )

    assert ordered.index(
        "validated_variant_registry"
    ) < ordered.index(
        "variant_review_board"
    )

    assert ordered.index(
        "variant_review_board"
    ) < ordered.index(
        "variant_decision_ledger"
    )


def test_snapshot_jobs_run_after_compiled_state():
    ordered = topological_order()

    assert ordered.index(
        "atlas_state_api"
    ) < ordered.index(
        "experiment_registry_snapshot"
    )

    assert ordered.index(
        "experiment_registry_snapshot"
    ) < ordered.index(
        "research_knowledge_graph_snapshot"
    )


def test_new_jobs_resolve_through_existing_safety_policy():
    command = resolve_registered_command(
        "research_evidence_accumulator"
    )

    assert command[1] == (
        "scripts/update_research_evidence_accumulator.py"
    )


def test_registry_contains_no_execution_or_deployment_jobs():
    for job in JOBS:
        normalized = job.command.lower()

        assert "live_execution" not in normalized
        assert "production_deploy" not in normalized
