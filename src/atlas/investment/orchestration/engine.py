"""Autonomous, dependency-ordered Atlas paper orchestration engine."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from atlas.investment.orchestration.allowlist import (
    build_command_registry,
    validate_execution_plan,
)
from atlas.investment.orchestration.contracts import (
    JobExecutionResult,
    ORCHESTRATION_CONTRACT_VERSION,
    OrchestrationPolicy,
    OrchestrationReport,
)
from atlas.investment.orchestration.runner import (
    ProcessRunner,
    SafeSubprocessRunner,
)


def execute_orchestration_plan(
    decision: Mapping[
        str,
        Any,
    ],
    *,
    project_root: Path,
    policy: OrchestrationPolicy | None = None,
    process_runner: ProcessRunner | None = None,
) -> dict[str, Any]:
    """Execute one validated scheduler plan in order."""
    effective_policy = (
        policy
        or OrchestrationPolicy()
    )

    runner = (
        process_runner
        or SafeSubprocessRunner()
    )

    started = datetime.now(
        UTC
    )

    decision_payload = dict(
        decision
    )

    errors: list[str] = []

    if not bool(
        decision_payload.get(
            "success",
            False,
        )
    ):
        errors.append(
            "SCHEDULER_DECISION_NOT_SUCCESSFUL"
        )

    scheduler_contract = dict(
        decision_payload.get(
            "contract",
            {},
        )
        or {}
    )

    if (
        effective_policy
        .require_scheduler_contract
    ):
        if not bool(
            scheduler_contract.get(
                "decision_only",
                False,
            )
        ):
            errors.append(
                "SCHEDULER_DECISION_CONTRACT_INVALID"
            )

        if not bool(
            scheduler_contract.get(
                "commands_not_executed",
                False,
            )
        ):
            errors.append(
                "SCHEDULER_COMMAND_BOUNDARY_INVALID"
            )

        if bool(
            scheduler_contract.get(
                "live_execution",
                False,
            )
        ):
            errors.append(
                "SCHEDULER_LIVE_EXECUTION_FORBIDDEN"
            )

    execution_plan = (
        decision_payload.get(
            "execution_plan",
            [],
        )
    )

    if not isinstance(
        execution_plan,
        list,
    ):
        errors.append(
            "EXECUTION_PLAN_NOT_LIST"
        )
        execution_plan = []

    if len(execution_plan) > int(
        effective_policy.maximum_jobs
    ):
        errors.append(
            "EXECUTION_PLAN_JOB_LIMIT_EXCEEDED"
        )

    registry = (
        build_command_registry()
    )

    validation = (
        validate_execution_plan(
            execution_plan,
            registry=registry,
        )
    )

    errors.extend(
        validation["errors"]
    )

    run_id = build_run_id(
        decision_payload
    )

    if errors:
        completed = datetime.now(
            UTC
        )

        return OrchestrationReport(
            success=False,
            version=(
                ORCHESTRATION_CONTRACT_VERSION
            ),
            run_id=run_id,
            decision_id=str(
                decision_payload.get(
                    "decision_id",
                    "",
                )
            ),
            started_at=(
                started.isoformat()
            ),
            completed_at=(
                completed.isoformat()
            ),
            status="REJECTED",
            counts={
                "planned": len(
                    execution_plan
                ),
                "completed": 0,
                "failed": 0,
                "blocked": 0,
                "rejected": len(
                    execution_plan
                ),
            },
            results=(),
            errors=tuple(
                errors
            ),
            contract=build_contract(),
        ).to_dict()

    results: list[
        dict[str, Any]
    ] = []

    failed_jobs: set[str] = set()
    completed_jobs: set[str] = set()

    dependency_map = build_dependency_map(
        decision_payload
    )

    for row in validation["rows"]:
        job_name = str(
            row["name"]
        )

        dependencies = tuple(
            dependency_map.get(
                job_name,
                (),
            )
        )

        blocked_by = tuple(
            dependency
            for dependency in dependencies
            if dependency in failed_jobs
        )

        if blocked_by:
            now = datetime.now(
                UTC
            )

            result = JobExecutionResult(
                job_name=job_name,
                status="BLOCKED",
                success=False,
                started_at=(
                    now.isoformat()
                ),
                completed_at=(
                    now.isoformat()
                ),
                elapsed_ms=0.0,
                return_code=None,
                stdout="",
                stderr="",
                error=(
                    "DEPENDENCY_FAILED"
                ),
                command=tuple(
                    row["command"]
                ),
                result_id=build_result_id(
                    run_id,
                    job_name,
                    "BLOCKED",
                ),
                blocked_by=(
                    blocked_by
                ),
            )

            results.append(
                result.to_dict()
            )

            failed_jobs.add(
                job_name
            )

            continue

        job_started = datetime.now(
            UTC
        )

        try:
            process_result = runner.run(
                row["command"],
                timeout_seconds=int(
                    row[
                        "timeout_seconds"
                    ]
                ),
                cwd=project_root,
            )

            success = (
                process_result.return_code
                == 0
            )

            status = (
                "COMPLETED"
                if success
                else "FAILED"
            )

            error = (
                ""
                if success
                else "PROCESS_RETURN_CODE:"
                + str(
                    process_result
                    .return_code
                )
            )

            stdout = truncate_output(
                process_result.stdout,
                limit=(
                    effective_policy
                    .maximum_output_characters
                ),
            )

            stderr = truncate_output(
                process_result.stderr,
                limit=(
                    effective_policy
                    .maximum_output_characters
                ),
            )

            return_code = (
                process_result.return_code
            )

            elapsed_ms = (
                process_result.elapsed_ms
            )

        except Exception as exception:
            success = False
            status = "FAILED"
            error = str(
                exception
            )
            stdout = ""
            stderr = ""
            return_code = None

            elapsed_ms = (
                datetime.now(UTC)
                - job_started
            ).total_seconds() * 1_000.0

        job_completed = datetime.now(
            UTC
        )

        result = JobExecutionResult(
            job_name=job_name,
            status=status,
            success=success,
            started_at=(
                job_started.isoformat()
            ),
            completed_at=(
                job_completed.isoformat()
            ),
            elapsed_ms=(
                elapsed_ms
            ),
            return_code=(
                return_code
            ),
            stdout=stdout,
            stderr=stderr,
            error=error,
            command=tuple(
                row["command"]
            ),
            result_id=build_result_id(
                run_id,
                job_name,
                status,
            ),
        )

        results.append(
            result.to_dict()
        )

        if success:
            completed_jobs.add(
                job_name
            )
        else:
            failed_jobs.add(
                job_name
            )

            if effective_policy.fail_fast:
                continue

    completed = datetime.now(
        UTC
    )

    completed_count = sum(
        1
        for result in results
        if result["status"]
        == "COMPLETED"
    )

    failed_count = sum(
        1
        for result in results
        if result["status"]
        == "FAILED"
    )

    blocked_count = sum(
        1
        for result in results
        if result["status"]
        == "BLOCKED"
    )

    successful = bool(
        not failed_count
        and not blocked_count
        and len(results)
        == len(
            validation["rows"]
        )
    )

    status = (
        "COMPLETED"
        if successful
        else "FAILED"
    )

    report = OrchestrationReport(
        success=successful,
        version=(
            ORCHESTRATION_CONTRACT_VERSION
        ),
        run_id=run_id,
        decision_id=str(
            decision_payload.get(
                "decision_id",
                "",
            )
        ),
        started_at=(
            started.isoformat()
        ),
        completed_at=(
            completed.isoformat()
        ),
        status=status,
        counts={
            "planned": len(
                validation["rows"]
            ),
            "completed": (
                completed_count
            ),
            "failed": (
                failed_count
            ),
            "blocked": (
                blocked_count
            ),
            "rejected": 0,
        },
        results=tuple(
            results
        ),
        errors=tuple(),
        contract=build_contract(),
    )

    return report.to_dict()


def build_dependency_map(
    decision: Mapping[
        str,
        Any,
    ],
) -> dict[str, tuple[str, ...]]:
    result: dict[
        str,
        tuple[str, ...]
    ] = {}

    for row in decision.get(
        "decisions",
        [],
    ):
        if not isinstance(
            row,
            Mapping,
        ):
            continue

        job = row.get(
            "job",
            {},
        )

        if not isinstance(
            job,
            Mapping,
        ):
            continue

        name = str(
            job.get(
                "name",
                "",
            )
        ).strip().upper()

        dependencies = tuple(
            str(value)
            .strip()
            .upper()
            for value
            in job.get(
                "dependencies",
                (),
            )
        )

        if name:
            result[name] = (
                dependencies
            )

    return result


def truncate_output(
    value: str,
    *,
    limit: int,
) -> str:
    text = str(
        value
        or ""
    )

    maximum = int(
        limit
    )

    if len(text) <= maximum:
        return text

    return (
        text[:maximum]
        + "\n...[TRUNCATED]"
    )


def build_run_id(
    decision: Mapping[
        str,
        Any,
    ],
) -> str:
    payload = {
        "decision_id": (
            decision.get(
                "decision_id",
                "",
            )
        ),
        "evaluated_at": (
            decision.get(
                "evaluated_at",
                "",
            )
        ),
        "due_jobs": (
            decision.get(
                "due_jobs",
                [],
            )
        ),
    }

    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

    return (
        "ORCHESTRATION-RUN-"
        + digest[:24]
    )


def build_result_id(
    run_id: str,
    job_name: str,
    status: str,
) -> str:
    digest = hashlib.sha256(
        (
            str(run_id)
            + ":"
            + str(job_name)
            + ":"
            + str(status)
        ).encode("utf-8")
    ).hexdigest()

    return (
        "ORCHESTRATION-RESULT-"
        + digest[:24]
    )


def build_contract() -> dict[str, Any]:
    return {
        "autonomous_orchestration": True,
        "allowlisted_commands_only": True,
        "dependency_ordered": True,
        "shell_execution": False,
        "paper_only": True,
        "submits_live_orders": False,
        "credentials_used": False,
        "live_execution": False,
    }


__all__ = [
    "execute_orchestration_plan",
]
