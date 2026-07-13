"""Canonical producer and output contracts for Atlas investment artifacts.

This module does not replace either canonical registry:

- ``atlas.investment.artifacts.ARTIFACTS`` owns stable artifact keys and paths.
- ``research_scheduler.JOBS`` owns jobs, commands, primary outputs, and DAG edges.

Artifact contracts connect those two registries and define which outputs must
exist before a job can be considered successfully healed.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from atlas.investment.artifacts import (
    ARTIFACTS,
)
from atlas.investment.research_scheduler import (
    JOBS,
    JOB_MAP,
)


@dataclass(frozen=True)
class JobArtifactContract:
    """Output obligations for one canonical research job."""

    job_id: str
    required_artifact_keys: tuple[str, ...] = ()
    optional_artifact_keys: tuple[str, ...] = ()
    require_primary_output: bool = True

    @property
    def primary_output_path(self) -> Path:
        return JOB_MAP[
            self.job_id
        ].output_path

    @property
    def required_paths(self) -> tuple[Path, ...]:
        paths: list[Path] = []

        if self.require_primary_output:
            paths.append(
                self.primary_output_path
            )

        for key in self.required_artifact_keys:
            paths.append(
                ARTIFACTS[key]
            )

        return deduplicate_paths(paths)

    @property
    def optional_paths(self) -> tuple[Path, ...]:
        return deduplicate_paths(
            ARTIFACTS[key]
            for key in self.optional_artifact_keys
        )


# Secondary artifacts that must be present for a complete successful build.
REQUIRED_SECONDARY_ARTIFACTS: dict[
    str,
    tuple[str, ...],
] = {
    "historical_alpha_engines": (
        "historical_alpha_engine_performance",
    ),
    "historical_alpha_validation": (
        "historical_alpha_validation_report",
    ),
    "meta_research": (
        "meta_hypotheses",
        "meta_research_priorities",
        "meta_failure_modes",
        "meta_family_gaps",
        "meta_feature_interactions",
    ),
    "hypothesis_validation": (
        "hypothesis_validation_results",
        "validated_hypotheses",
        "hypothesis_validation_folds",
    ),
    "adaptive_research_prioritizer": (
        "research_priority_queue",
        "research_candidate_scores",
        "research_score_components",
        "research_priority_explanations",
        "research_duplication_flags",
    ),
    "research_candidate_consolidator": (
        "consolidated_research_programs",
        "research_program_members",
        "research_program_dimensions",
        "research_program_conflicts",
        "research_candidate_consolidator_report",
    ),
    "research_program_manager": (
        "research_program_registry",
        "research_program_history",
        "research_program_recommendations",
        "research_program_manager_report",
    ),
    "research_experiment_designer": (
        "research_experiment_designs",
        "research_experiment_hypotheses",
        "research_experiment_variants",
        "research_experiment_walk_forward_plan",
        "research_experiment_acceptance_criteria",
        "research_experiment_design_validation",
        "research_experiment_designer_report",
    ),
    "research_experiment_execution": (
        "research_execution_runs",
        "research_execution_fold_results",
        "research_execution_variant_results",
        "research_execution_acceptance_results",
        "research_execution_evidence_summary",
        "research_execution_report",
    ),
    "research_evidence_accumulator": (
        "accumulated_experiment_evidence",
        "accumulated_variant_evidence",
        "evidence_run_lineage",
        "evidence_consistency",
        "evidence_sufficiency",
        "evidence_program_recommendations",
        "evidence_history",
        "research_evidence_accumulator_state",
        "research_evidence_accumulator_report",
    ),
    "validated_variant_registry": (
        "validated_variant_registry",
    ),
    "variant_review_board": (
        "variant_review_board",
        "variant_review_conflicts",
    ),
    "variant_decision_ledger": (
        "variant_decision_ledger",
        "variant_implementation_queue",
    ),
    "variant_implementation_planner": (
        "variant_implementation_plans",
    ),
    "portfolio_promotion_lab_v1": (
        "portfolio_promotion_v1_decision",
    ),
    "portfolio_promotion_lab_v2": (
        "portfolio_promotion_v2_decision",
    ),
    "regime_intelligence": (
        "regime_report",
    ),
    "macro_regime_fusion": (
        "macro_regime_fusion_report",
    ),
    "atlas_compiler": (
        "atlas_compiler_report",
    ),
    "experiment_registry_snapshot": (
        "experiment_registry",
        "experiment_observations",
        "experiment_metrics",
        "experiment_artifacts",
        "experiment_relationships",
        "experiment_status_history",
        "experiment_orchestrator_runs",
    ),
    "research_knowledge_graph_snapshot": (
        "knowledge_graph_nodes",
        "knowledge_graph_edges",
        "knowledge_graph_metrics",
    ),
}


# Diagnostics that may legitimately be empty or absent in valid runs.
OPTIONAL_SECONDARY_ARTIFACTS: dict[
    str,
    tuple[str, ...],
] = {
    "research_evidence_accumulator": (
        "evidence_decay",
        "evidence_contradictions",
    ),
    "research_scheduler": (
        "research_scheduler_schedule",
    ),
    "research_orchestrator": (
        "research_orchestrator_history",
        "research_orchestrator_report",
    ),
}


def build_contracts() -> tuple[JobArtifactContract, ...]:
    """Build one immutable output contract per canonical job."""
    contracts: list[
        JobArtifactContract
    ] = []

    for job in JOBS:
        contracts.append(
            JobArtifactContract(
                job_id=job.job_id,
                required_artifact_keys=(
                    REQUIRED_SECONDARY_ARTIFACTS.get(
                        job.job_id,
                        (),
                    )
                ),
                optional_artifact_keys=(
                    OPTIONAL_SECONDARY_ARTIFACTS.get(
                        job.job_id,
                        (),
                    )
                ),
                require_primary_output=True,
            )
        )

    return tuple(contracts)


CONTRACTS = build_contracts()

CONTRACT_MAP = {
    contract.job_id: contract
    for contract in CONTRACTS
}


def contract_for_job(
    job_id: str,
) -> JobArtifactContract:
    """Return the canonical artifact contract for one job."""
    try:
        return CONTRACT_MAP[
            str(job_id)
        ]
    except KeyError as error:
        raise KeyError(
            "Unknown artifact contract job: "
            f"{job_id}"
        ) from error


def validate_contract_registry() -> list[str]:
    """Return structural contract errors without reading output files."""
    errors: list[str] = []

    job_ids = {
        job.job_id
        for job in JOBS
    }

    seen_contracts: set[str] = set()
    producer_by_key: dict[str, str] = {}
    producer_by_path: dict[Path, str] = {}

    for contract in CONTRACTS:
        if contract.job_id in seen_contracts:
            errors.append(
                "DUPLICATE_JOB_CONTRACT:"
                f"{contract.job_id}"
            )
        else:
            seen_contracts.add(
                contract.job_id
            )

        if contract.job_id not in job_ids:
            errors.append(
                "UNKNOWN_CONTRACT_JOB:"
                f"{contract.job_id}"
            )
            continue

        overlap = (
            set(
                contract.required_artifact_keys
            )
            & set(
                contract.optional_artifact_keys
            )
        )

        for key in sorted(overlap):
            errors.append(
                "REQUIRED_OPTIONAL_OVERLAP:"
                f"{contract.job_id}:{key}"
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
            for key in keys:
                if key not in ARTIFACTS:
                    errors.append(
                        "UNKNOWN_ARTIFACT_KEY:"
                        f"{contract.job_id}:"
                        f"{requirement}:{key}"
                    )
                    continue

                existing_key_owner = (
                    producer_by_key.get(key)
                )

                if (
                    existing_key_owner is not None
                    and existing_key_owner
                    != contract.job_id
                ):
                    errors.append(
                        "DUPLICATE_ARTIFACT_PRODUCER:"
                        f"{key}:"
                        f"{existing_key_owner}:"
                        f"{contract.job_id}"
                    )
                else:
                    producer_by_key[
                        key
                    ] = contract.job_id

        for path in contract.required_paths:
            normalized = normalize_path(
                path
            )

            existing_path_owner = (
                producer_by_path.get(
                    normalized
                )
            )

            if (
                existing_path_owner is not None
                and existing_path_owner
                != contract.job_id
            ):
                errors.append(
                    "DUPLICATE_PATH_PRODUCER:"
                    f"{normalized}:"
                    f"{existing_path_owner}:"
                    f"{contract.job_id}"
                )
            else:
                producer_by_path[
                    normalized
                ] = contract.job_id

    missing_job_contracts = (
        job_ids - seen_contracts
    )

    for job_id in sorted(
        missing_job_contracts
    ):
        errors.append(
            f"MISSING_JOB_CONTRACT:{job_id}"
        )

    return sorted(set(errors))


def validate_job_outputs(
    job_id: str,
) -> dict[str, Any]:
    """Validate required and optional outputs for one canonical job."""
    contract = contract_for_job(
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
        "required_output_count": len(
            required_checks
        ),
        "optional_output_count": len(
            optional_checks
        ),
        "valid_required_output_count": (
            len(required_checks)
            - len(required_failures)
        ),
        "missing_or_invalid_required_count": (
            len(required_failures)
        ),
        "invalid_optional_count": len(
            optional_failures
        ),
        "required_checks": (
            required_checks
        ),
        "optional_checks": (
            optional_checks
        ),
        "required_failures": (
            required_failures
        ),
        "optional_failures": (
            optional_failures
        ),
    }


def inspect_output(
    path: Path,
    *,
    required: bool,
) -> dict[str, Any]:
    """Validate one output using extension-appropriate structural checks."""
    normalized = normalize_path(path)

    result = {
        "path": str(normalized),
        "required": bool(required),
        "exists": False,
        "is_file": False,
        "nonempty": False,
        "readable": False,
        "valid": False,
        "format": (
            normalized.suffix.lower()
            or "unknown"
        ),
        "error": "",
    }

    if not normalized.exists():
        result["error"] = (
            "REQUIRED_OUTPUT_MISSING"
            if required
            else "OPTIONAL_OUTPUT_MISSING"
        )
        return result

    result["exists"] = True

    if not normalized.is_file():
        result["error"] = (
            "OUTPUT_NOT_FILE"
        )
        return result

    result["is_file"] = True

    try:
        size = normalized.stat().st_size
    except OSError as error:
        result["error"] = (
            f"{type(error).__name__}: {error}"
        )
        return result

    result["size_bytes"] = int(size)
    result["nonempty"] = size > 0

    if size <= 0:
        result["error"] = (
            "OUTPUT_EMPTY"
        )
        return result

    suffix = normalized.suffix.lower()

    try:
        if suffix == ".json":
            payload = json.loads(
                normalized.read_text(
                    encoding="utf-8"
                )
            )

            if not isinstance(
                payload,
                (dict, list),
            ):
                result["error"] = (
                    "JSON_ROOT_INVALID"
                )
                return result

        elif suffix == ".csv":
            with normalized.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as handle:
                reader = csv.reader(handle)

                try:
                    header = next(reader)
                except StopIteration:
                    result["error"] = (
                        "CSV_EMPTY"
                    )
                    return result

                if not header:
                    result["error"] = (
                        "CSV_HEADER_MISSING"
                    )
                    return result

        else:
            with normalized.open(
                "rb"
            ) as handle:
                handle.read(1)

        result["readable"] = True
        result["valid"] = True

    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        csv.Error,
    ) as error:
        result["error"] = (
            f"{type(error).__name__}: {error}"
        )

    return result


def producer_for_artifact_key(
    artifact_key: str,
) -> str:
    """Return the declared producer job for one registered artifact key."""
    producers = [
        contract.job_id
        for contract in CONTRACTS
        if (
            artifact_key
            in contract.required_artifact_keys
            or artifact_key
            in contract.optional_artifact_keys
        )
    ]

    if not producers:
        return ""

    if len(producers) > 1:
        raise ValueError(
            "Artifact has multiple producers: "
            f"{artifact_key}:"
            f"{'|'.join(sorted(producers))}"
        )

    return producers[0]


def build_contract_audit() -> dict[str, Any]:
    """Build a complete structural and filesystem output-contract audit."""
    registry_errors = (
        validate_contract_registry()
    )

    job_results = [
        validate_job_outputs(
            contract.job_id
        )
        for contract in CONTRACTS
    ]

    failed_jobs = [
        result
        for result in job_results
        if not result["success"]
    ]

    assigned_keys = {
        key
        for contract in CONTRACTS
        for key in (
            contract.required_artifact_keys
            + contract.optional_artifact_keys
        )
    }

    unassigned_keys = sorted(
        set(ARTIFACTS)
        - assigned_keys
    )

    return {
        "success": bool(
            not registry_errors
        ),
        "filesystem_complete": bool(
            not failed_jobs
        ),
        "contract_count": len(
            CONTRACTS
        ),
        "registered_job_count": len(
            JOBS
        ),
        "registered_artifact_count": len(
            ARTIFACTS
        ),
        "assigned_artifact_count": len(
            assigned_keys
        ),
        "unassigned_artifact_count": len(
            unassigned_keys
        ),
        "registry_errors": registry_errors,
        "unassigned_artifact_keys": (
            unassigned_keys
        ),
        "failed_job_contracts": [
            result["job_id"]
            for result in failed_jobs
        ],
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
    "CONTRACTS",
    "CONTRACT_MAP",
    "JobArtifactContract",
    "OPTIONAL_SECONDARY_ARTIFACTS",
    "REQUIRED_SECONDARY_ARTIFACTS",
    "build_contract_audit",
    "build_contracts",
    "contract_for_job",
    "inspect_output",
    "producer_for_artifact_key",
    "validate_contract_registry",
    "validate_job_outputs",
]
