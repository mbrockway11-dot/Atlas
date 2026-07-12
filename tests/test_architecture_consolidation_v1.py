"""Regression tests for Atlas Architecture Consolidation Phase A."""

from __future__ import annotations

from scripts.audit_architecture_consolidation import run_audit
from atlas.investment.artifacts import artifact_path, validate_registry
from atlas.investment.research_evidence_accumulator.config import (
    EXPERIMENT_EVIDENCE_CSV,
    REPORT_JSON as ACCUMULATOR_REPORT_JSON,
    VARIANT_EVIDENCE_CSV,
)
from atlas.investment.research_experiment_designer.config import (
    ACCEPTANCE_CSV,
    DESIGNS_CSV,
    REPORT_JSON as DESIGNER_REPORT_JSON,
    VALIDATION_CSV,
    VARIANTS_CSV,
    WALK_FORWARD_CSV,
)
from atlas.investment.research_experiment_execution.config import (
    ACCEPTANCE_RESULTS_CSV,
    EVIDENCE_SUMMARY_CSV,
    FOLD_RESULTS_CSV,
    REPORT_JSON as EXECUTION_REPORT_JSON,
    RUNS_CSV,
    VARIANT_RESULTS_CSV,
)
from atlas.investment.research_scheduler import JOBS, topological_order


def test_artifact_registry_is_structurally_valid():
    assert validate_registry() == []


def test_designer_artifacts_match_config_contract():
    assert artifact_path("research_experiment_designs") == DESIGNS_CSV
    assert artifact_path("research_experiment_variants") == VARIANTS_CSV
    assert artifact_path("research_experiment_walk_forward_plan") == WALK_FORWARD_CSV
    assert artifact_path("research_experiment_acceptance_criteria") == ACCEPTANCE_CSV
    assert artifact_path("research_experiment_design_validation") == VALIDATION_CSV
    assert artifact_path("research_experiment_designer_report") == DESIGNER_REPORT_JSON


def test_execution_artifacts_match_config_contract():
    assert artifact_path("research_execution_runs") == RUNS_CSV
    assert artifact_path("research_execution_fold_results") == FOLD_RESULTS_CSV
    assert artifact_path("research_execution_variant_results") == VARIANT_RESULTS_CSV
    assert artifact_path("research_execution_acceptance_results") == ACCEPTANCE_RESULTS_CSV
    assert artifact_path("research_execution_evidence_summary") == EVIDENCE_SUMMARY_CSV
    assert artifact_path("research_execution_report") == EXECUTION_REPORT_JSON


def test_accumulator_artifacts_match_config_contract():
    assert artifact_path("accumulated_experiment_evidence") == EXPERIMENT_EVIDENCE_CSV
    assert artifact_path("accumulated_variant_evidence") == VARIANT_EVIDENCE_CSV
    assert artifact_path("research_evidence_accumulator_report") == ACCUMULATOR_REPORT_JSON


def test_canonical_job_dag_covers_every_registered_job_once():
    job_ids = [job.job_id for job in JOBS]
    ordered = topological_order()

    assert len(job_ids) == len(set(job_ids))
    assert len(ordered) == len(job_ids)
    assert set(ordered) == set(job_ids)


def test_architecture_audit_passes():
    assert run_audit() == []
