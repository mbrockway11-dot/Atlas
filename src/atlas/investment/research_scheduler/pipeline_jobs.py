"""Additional Atlas research-program and evidence jobs.

These jobs extend the mature scheduler registry without duplicating its
existing market, variant-governance, portfolio, compiler, or API stages.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable


def build_pipeline_jobs(job_spec: Callable):
    """Build the research-program and evidence stages."""
    return (
        job_spec(
            job_id="adaptive_research_prioritizer",
            title="Update Adaptive Research Prioritizer",
            command=(
                "python scripts/"
                "update_adaptive_research_prioritizer.py"
            ),
            output_path=Path(
                "output/investment_adaptive_research_prioritizer/"
                "research_prioritizer_report.json"
            ),
            dependencies=("meta_research",),
            priority="MEDIUM",
            stale_after_hours=168.0,
            category="research_programs",
        ),
        job_spec(
            job_id="research_candidate_consolidator",
            title="Update Research Candidate Consolidator",
            command=(
                "python scripts/"
                "update_research_candidate_consolidator.py"
            ),
            output_path=Path(
                "output/investment_research_candidate_consolidator/"
                "research_candidate_consolidator_report.json"
            ),
            dependencies=("adaptive_research_prioritizer",),
            priority="MEDIUM",
            stale_after_hours=168.0,
            category="research_programs",
        ),
        job_spec(
            job_id="research_program_manager",
            title="Update Research Program Manager",
            command=(
                "python scripts/update_research_program_manager.py"
            ),
            output_path=Path(
                "output/investment_research_program_manager/"
                "research_program_manager_report.json"
            ),
            dependencies=("research_candidate_consolidator",),
            priority="MEDIUM",
            stale_after_hours=168.0,
            category="research_programs",
        ),
        job_spec(
            job_id="research_experiment_designer",
            title="Update Research Experiment Designer",
            command=(
                "python scripts/"
                "update_research_experiment_designer.py"
            ),
            output_path=Path(
                "output/investment_research_experiment_designer/"
                "research_experiment_designer_report.json"
            ),
            dependencies=("research_program_manager",),
            priority="MEDIUM",
            stale_after_hours=168.0,
            category="research_programs",
        ),
        job_spec(
            job_id="research_experiment_execution",
            title="Run Research Experiment Execution Lab",
            command=(
                "python scripts/"
                "run_research_experiment_execution.py"
            ),
            output_path=Path(
                "output/investment_research_experiment_execution/"
                "experiment_execution_report.json"
            ),
            dependencies=(
                "research_experiment_designer",
                "historical_alpha_validation",
            ),
            priority="MEDIUM",
            stale_after_hours=168.0,
            category="research_programs",
        ),
        job_spec(
            job_id="research_evidence_accumulator",
            title="Update Research Evidence Accumulator",
            command=(
                "python scripts/"
                "update_research_evidence_accumulator.py"
            ),
            output_path=Path(
                "output/investment_research_evidence_accumulator/"
                "research_evidence_accumulator_report.json"
            ),
            dependencies=("research_experiment_execution",),
            priority="MEDIUM",
            stale_after_hours=168.0,
            category="research_programs",
        ),
        job_spec(
            job_id="experiment_registry_snapshot",
            title="Update Experiment Registry Snapshot",
            command="python scripts/update_experiment_registry.py",
            output_path=Path(
                "output/investment_experiment_registry/"
                "experiment_registry_report.json"
            ),
            dependencies=(
                "atlas_state_api",
                "research_evidence_accumulator",
                "variant_decision_ledger",
            ),
            priority="LOW",
            stale_after_hours=168.0,
            category="research_snapshots",
        ),
        job_spec(
            job_id="research_knowledge_graph_snapshot",
            title="Update Research Knowledge Graph Snapshot",
            command=(
                "python scripts/"
                "update_research_knowledge_graph.py"
            ),
            output_path=Path(
                "output/investment_research_knowledge_graph/"
                "knowledge_graph_report.json"
            ),
            dependencies=(
                "experiment_registry_snapshot",
                "atlas_state_api",
            ),
            priority="LOW",
            stale_after_hours=168.0,
            category="research_snapshots",
        ),
    )


def compose_jobs(
    legacy_jobs: Iterable,
    job_spec: Callable,
):
    """Compose one acyclic registry and refresh evidence dependencies."""
    replacements = {
        "validated_variant_registry": (
            "hypothesis_validation",
            "research_evidence_accumulator",
        ),
        "variant_review_board": (
            "validated_variant_registry",
            "research_evidence_accumulator",
            "governance_snapshots",
            "learning_engine",
        ),
    }

    composed = []
    for job in legacy_jobs:
        dependencies = replacements.get(
            job.job_id,
            job.dependencies,
        )
        composed.append(
            job_spec(
                job_id=job.job_id,
                title=job.title,
                command=job.command,
                output_path=job.output_path,
                dependencies=tuple(dependencies),
                priority=job.priority,
                stale_after_hours=job.stale_after_hours,
                enabled=job.enabled,
                category=job.category,
            )
        )

    insert_before = next(
        index
        for index, job in enumerate(composed)
        if job.job_id == "validated_variant_registry"
    )
    active_jobs = build_pipeline_jobs(job_spec)[:6]
    snapshot_jobs = build_pipeline_jobs(job_spec)[6:]

    composed[
        insert_before:insert_before
    ] = list(active_jobs)
    composed.extend(snapshot_jobs)

    job_ids = [job.job_id for job in composed]
    if len(job_ids) != len(set(job_ids)):
        raise ValueError(
            "Canonical scheduler registry contains duplicate job IDs."
        )

    return tuple(composed)
