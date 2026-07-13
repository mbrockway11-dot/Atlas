"""Canonical input-lineage contracts for Atlas investment research.

This module connects the existing canonical registries:

- research jobs own commands, primary outputs, and dependency edges;
- artifact contracts own producer/output obligations;
- the artifact registry owns stable artifact keys and paths.

No second execution DAG is defined here. Input-lineage contracts describe which
artifacts flow across the already-canonical job dependency graph.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from atlas.investment.artifact_contracts import (
    CONTRACT_MAP,
    inspect_output,
    producer_for_artifact_key,
)
from atlas.investment.artifacts import (
    ARTIFACTS,
)
from atlas.investment.research_scheduler import (
    JOBS,
    JOB_MAP,
)


@dataclass(frozen=True)
class JobInputContract:
    """Declared artifact inputs for one canonical job."""

    job_id: str
    required_artifact_keys: tuple[str, ...] = ()
    optional_artifact_keys: tuple[str, ...] = ()
    inherit_dependency_primary_outputs: bool = True

    @property
    def dependency_job_ids(self) -> tuple[str, ...]:
        return tuple(
            JOB_MAP[self.job_id].dependencies
        )

    @property
    def inherited_primary_paths(self) -> tuple[Path, ...]:
        if not self.inherit_dependency_primary_outputs:
            return ()

        return deduplicate_paths(
            JOB_MAP[dependency_id].output_path
            for dependency_id
            in self.dependency_job_ids
        )

    @property
    def required_paths(self) -> tuple[Path, ...]:
        return deduplicate_paths(
            (
                *self.inherited_primary_paths,
                *(
                    ARTIFACTS[key]
                    for key
                    in self.required_artifact_keys
                ),
            )
        )

    @property
    def optional_paths(self) -> tuple[Path, ...]:
        return deduplicate_paths(
            ARTIFACTS[key]
            for key
            in self.optional_artifact_keys
        )


# Explicit secondary inputs supplement direct dependency primary outputs.
# Producer alignment is validated against the canonical upstream closure.
REQUIRED_INPUT_ARTIFACTS: dict[
    str,
    tuple[str, ...],
] = {
    "historical_alpha_validation": (
        "historical_alpha_engine_performance",
    ),
    "alpha_research_lab": (
        "historical_alpha_engine_performance",
        "historical_alpha_validation_report",
        "macro_regime_fusion_report",
    ),
    "hypothesis_validation": (
        "meta_hypotheses",
        "meta_research_priorities",
    ),
    "adaptive_research_prioritizer": (
        "meta_hypotheses",
        "meta_research_priorities",
        "meta_failure_modes",
        "meta_family_gaps",
    ),
    "research_candidate_consolidator": (
        "research_priority_queue",
        "research_candidate_scores",
        "research_score_components",
        "research_priority_explanations",
        "research_duplication_flags",
    ),
    "research_program_manager": (
        "consolidated_research_programs",
        "research_program_members",
        "research_program_dimensions",
        "research_program_conflicts",
    ),
    "research_experiment_designer": (
        "research_program_registry",
        "research_program_recommendations",
    ),
    "research_experiment_execution": (
        "research_experiment_designs",
        "research_experiment_hypotheses",
        "research_experiment_variants",
        "research_experiment_walk_forward_plan",
        "research_experiment_acceptance_criteria",
        "research_experiment_design_validation",
    ),
    "research_evidence_accumulator": (
        "research_execution_runs",
        "research_execution_fold_results",
        "research_execution_variant_results",
        "research_execution_acceptance_results",
        "research_execution_evidence_summary",
    ),
    "validated_variant_registry": (
        "accumulated_variant_evidence",
        "evidence_consistency",
        "evidence_sufficiency",
        "validated_hypotheses",
    ),
    "variant_review_board": (
        "validated_variant_registry",
        "accumulated_variant_evidence",
        "evidence_consistency",
        "evidence_sufficiency",
    ),
    "variant_decision_ledger": (
        "variant_review_board",
        "variant_review_conflicts",
    ),
    "variant_implementation_planner": (
        "variant_decision_ledger",
        "variant_implementation_queue",
    ),
    "experiment_registry_snapshot": (
        "research_execution_runs",
        "research_execution_variant_results",
        "accumulated_experiment_evidence",
        "accumulated_variant_evidence",
        "variant_decision_ledger",
        "variant_implementation_plans",
    ),
    "research_knowledge_graph_snapshot": (
        "experiment_registry",
        "experiment_observations",
        "experiment_metrics",
        "experiment_artifacts",
        "experiment_relationships",
        "validated_variant_registry",
        "variant_decision_ledger",
    ),
}


OPTIONAL_INPUT_ARTIFACTS: dict[
    str,
    tuple[str, ...],
] = {
    "variant_review_board": (
        "evidence_contradictions",
    ),
}


def build_input_contracts() -> tuple[JobInputContract, ...]:
    """Build one immutable input contract for every canonical job."""
    return tuple(
        JobInputContract(
            job_id=job.job_id,
            required_artifact_keys=(
                REQUIRED_INPUT_ARTIFACTS.get(
                    job.job_id,
                    (),
                )
            ),
            optional_artifact_keys=(
                OPTIONAL_INPUT_ARTIFACTS.get(
                    job.job_id,
                    (),
                )
            ),
            inherit_dependency_primary_outputs=True,
        )
        for job in JOBS
    )


INPUT_CONTRACTS = build_input_contracts()

INPUT_CONTRACT_MAP = {
    contract.job_id: contract
    for contract in INPUT_CONTRACTS
}


def input_contract_for_job(
    job_id: str,
) -> JobInputContract:
    """Return the canonical input contract for one job."""
    try:
        return INPUT_CONTRACT_MAP[
            str(job_id)
        ]
    except KeyError as error:
        raise KeyError(
            "Unknown input-lineage job: "
            f"{job_id}"
        ) from error


def upstream_job_closure(
    job_id: str,
) -> set[str]:
    """Return every transitive upstream job using canonical dependencies."""
    if job_id not in JOB_MAP:
        raise KeyError(
            f"Unknown canonical job: {job_id}"
        )

    discovered: set[str] = set()
    pending = list(
        JOB_MAP[job_id].dependencies
    )

    while pending:
        dependency_id = pending.pop()

        if dependency_id in discovered:
            continue

        discovered.add(
            dependency_id
        )

        dependency_job = JOB_MAP.get(
            dependency_id
        )

        if dependency_job is not None:
            pending.extend(
                dependency_job.dependencies
            )

    return discovered


def validate_lineage_registry() -> list[str]:
    """Return structural input-lineage errors without reading output files."""
    errors: list[str] = []

    job_ids = {
        job.job_id
        for job in JOBS
    }

    seen_jobs: set[str] = set()

    for contract in INPUT_CONTRACTS:
        job_id = contract.job_id

        if job_id in seen_jobs:
            errors.append(
                f"DUPLICATE_INPUT_CONTRACT:{job_id}"
            )
        else:
            seen_jobs.add(job_id)

        if job_id not in job_ids:
            errors.append(
                f"UNKNOWN_INPUT_CONTRACT_JOB:{job_id}"
            )
            continue

        required_keys = set(
            contract.required_artifact_keys
        )
        optional_keys = set(
            contract.optional_artifact_keys
        )

        for key in sorted(
            required_keys & optional_keys
        ):
            errors.append(
                "REQUIRED_OPTIONAL_INPUT_OVERLAP:"
                f"{job_id}:{key}"
            )

        upstream = upstream_job_closure(
            job_id
        )

        for requirement, keys in (
            (
                "required",
                contract.required_artifact_keys,
            ),
            (
                "optional",
                contract.optional_artifact_keys,
            ),
        ):
            seen_keys: set[str] = set()

            for key in keys:
                if key in seen_keys:
                    errors.append(
                        "DUPLICATE_INPUT_KEY:"
                        f"{job_id}:{requirement}:{key}"
                    )
                    continue

                seen_keys.add(key)

                if key not in ARTIFACTS:
                    errors.append(
                        "UNKNOWN_INPUT_ARTIFACT:"
                        f"{job_id}:{requirement}:{key}"
                    )
                    continue

                producer = producer_for_artifact_key(
                    key
                )

                if not producer:
                    errors.append(
                        "INPUT_WITHOUT_PRODUCER:"
                        f"{job_id}:{key}"
                    )
                    continue

                if producer == job_id:
                    errors.append(
                        "SELF_CONSUMED_ARTIFACT:"
                        f"{job_id}:{key}"
                    )
                    continue

                if producer not in upstream:
                    errors.append(
                        "INPUT_PRODUCER_NOT_UPSTREAM:"
                        f"{job_id}:{key}:{producer}"
                    )

    for missing_job_id in sorted(
        job_ids - seen_jobs
    ):
        errors.append(
            "MISSING_INPUT_CONTRACT:"
            f"{missing_job_id}"
        )

    return sorted(set(errors))


def build_lineage_edges() -> list[dict[str, Any]]:
    """Build canonical producer-to-consumer artifact lineage edges."""
    rows: list[dict[str, Any]] = []

    for contract in INPUT_CONTRACTS:
        consumer_id = contract.job_id

        if contract.inherit_dependency_primary_outputs:
            for dependency_id in (
                contract.dependency_job_ids
            ):
                dependency_job = JOB_MAP[
                    dependency_id
                ]

                rows.append({
                    "producer_job_id": (
                        dependency_id
                    ),
                    "consumer_job_id": (
                        consumer_id
                    ),
                    "artifact_key": "",
                    "artifact_path": str(
                        normalize_path(
                            dependency_job.output_path
                        )
                    ),
                    "requirement": "required",
                    "lineage_source": (
                        "dependency_primary_output"
                    ),
                    "direct_dependency": True,
                })

        for requirement, keys in (
            (
                "required",
                contract.required_artifact_keys,
            ),
            (
                "optional",
                contract.optional_artifact_keys,
            ),
        ):
            for key in keys:
                producer = (
                    producer_for_artifact_key(
                        key
                    )
                )

                rows.append({
                    "producer_job_id": producer,
                    "consumer_job_id": (
                        consumer_id
                    ),
                    "artifact_key": key,
                    "artifact_path": str(
                        normalize_path(
                            ARTIFACTS[key]
                        )
                    ),
                    "requirement": (
                        requirement
                    ),
                    "lineage_source": (
                        "explicit_artifact_key"
                    ),
                    "direct_dependency": bool(
                        producer
                        in contract.dependency_job_ids
                    ),
                })

    return deduplicate_edge_rows(rows)


def validate_job_inputs(
    job_id: str,
) -> dict[str, Any]:
    """Inspect required and optional input artifacts for one job."""
    contract = input_contract_for_job(
        job_id
    )

    required_checks = [
        inspect_output(
            path,
            required=True,
        )
        for path in contract.required_paths
    ]

    optional_checks = [
        inspect_output(
            path,
            required=False,
        )
        for path in contract.optional_paths
    ]

    required_failures = [
        check
        for check in required_checks
        if not check["valid"]
    ]

    optional_failures = [
        check
        for check in optional_checks
        if (
            check["exists"]
            and not check["valid"]
        )
    ]

    return {
        "job_id": contract.job_id,
        "success": not required_failures,
        "required_input_count": len(
            required_checks
        ),
        "optional_input_count": len(
            optional_checks
        ),
        "valid_required_input_count": (
            len(required_checks)
            - len(required_failures)
        ),
        "missing_or_invalid_required_count": (
            len(required_failures)
        ),
        "invalid_optional_count": len(
            optional_failures
        ),
        "required_checks": required_checks,
        "optional_checks": optional_checks,
        "required_failures": (
            required_failures
        ),
        "optional_failures": (
            optional_failures
        ),
    }


def build_lineage_audit() -> dict[str, Any]:
    """Build a structural and filesystem input-lineage audit."""
    registry_errors = (
        validate_lineage_registry()
    )

    job_results = [
        validate_job_inputs(
            contract.job_id
        )
        for contract in INPUT_CONTRACTS
    ]

    incomplete_jobs = [
        result
        for result in job_results
        if not result["success"]
    ]

    edges = build_lineage_edges()

    explicit_keys = {
        key
        for contract in INPUT_CONTRACTS
        for key in (
            contract.required_artifact_keys
            + contract.optional_artifact_keys
        )
    }

    return {
        "success": not registry_errors,
        "filesystem_complete": (
            not incomplete_jobs
        ),
        "input_contract_count": len(
            INPUT_CONTRACTS
        ),
        "registered_job_count": len(
            JOBS
        ),
        "lineage_edge_count": len(edges),
        "explicit_input_artifact_count": len(
            explicit_keys
        ),
        "registry_errors": registry_errors,
        "incomplete_job_inputs": [
            result["job_id"]
            for result in incomplete_jobs
        ],
        "edges": edges,
        "jobs": job_results,
    }


def deduplicate_paths(
    paths: Iterable[Path],
) -> tuple[Path, ...]:
    seen: set[Path] = set()
    ordered: list[Path] = []

    for path in paths:
        normalized = normalize_path(
            path
        )

        if normalized in seen:
            continue

        seen.add(normalized)
        ordered.append(normalized)

    return tuple(ordered)


def deduplicate_edge_rows(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    seen: set[tuple[str, ...]] = set()
    result: list[dict[str, Any]] = []

    for source in rows:
        row = dict(source)

        identity = (
            str(row["producer_job_id"]),
            str(row["consumer_job_id"]),
            str(row["artifact_key"]),
            str(row["artifact_path"]),
            str(row["requirement"]),
        )

        if identity in seen:
            continue

        seen.add(identity)
        result.append(row)

    return result


def normalize_path(
    path: Path,
) -> Path:
    return Path(
        str(path).replace(
            "\\",
            "/",
        )
    )


__all__ = [
    "INPUT_CONTRACTS",
    "INPUT_CONTRACT_MAP",
    "JobInputContract",
    "OPTIONAL_INPUT_ARTIFACTS",
    "REQUIRED_INPUT_ARTIFACTS",
    "build_input_contracts",
    "build_lineage_audit",
    "build_lineage_edges",
    "input_contract_for_job",
    "upstream_job_closure",
    "validate_job_inputs",
    "validate_lineage_registry",
]
