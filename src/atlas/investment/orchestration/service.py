"""Restart-safe service for Atlas autonomous paper orchestration."""

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
    OrchestrationPolicy,
)
from atlas.investment.orchestration.engine import (
    execute_orchestration_plan,
)
from atlas.investment.orchestration.persistence import (
    LATEST_ORCHESTRATION_REPORT_JSON,
    ORCHESTRATION_CHECKPOINT_JSON,
    ORCHESTRATION_HISTORY_JSONL,
    load_orchestration_checkpoint,
    write_orchestration_outputs,
)
from atlas.investment.orchestration.runner import (
    ProcessRunner,
)
from atlas.investment.orchestration.state import (
    OrchestrationRuntimeConfig,
    materialize_execution_plan,
    validate_runtime_files,
)


ORCHESTRATION_SERVICE_VERSION = "1.0.0"


def run_orchestration_service(
    decision: Mapping[
        str,
        Any,
    ],
    *,
    runtime: OrchestrationRuntimeConfig,
    project_root: Path,
    dry_run: bool = True,
    resume: bool = True,
    policy: OrchestrationPolicy | None = None,
    process_runner: ProcessRunner | None = None,
    write_outputs: bool = True,
    report_path: Path = (
        LATEST_ORCHESTRATION_REPORT_JSON
    ),
    checkpoint_path: Path = (
        ORCHESTRATION_CHECKPOINT_JSON
    ),
    history_path: Path = (
        ORCHESTRATION_HISTORY_JSONL
    ),
) -> dict[str, Any]:
    """Validate, dry-run, resume, or execute one scheduler decision."""
    root = Path(
        project_root
    ).resolve()

    started_at = datetime.now(
        UTC
    ).isoformat()

    materialized = (
        materialize_execution_plan(
            decision,
            runtime=runtime,
        )
    )

    decision_id = str(
        materialized.get(
            "decision_id",
            "",
        )
    )

    service_run_id = (
        build_service_run_id(
            materialized,
            runtime=runtime,
            dry_run=dry_run,
        )
    )

    runtime_validation = (
        validate_runtime_files(
            runtime,
            project_root=root,
        )
    )

    registry = (
        build_command_registry()
    )

    plan_validation = (
        validate_execution_plan(
            materialized.get(
                "execution_plan",
                [],
            ),
            registry=registry,
        )
    )

    errors = [
        *runtime_validation[
            "errors"
        ],
        *plan_validation[
            "errors"
        ],
    ]

    checkpoint = (
        load_orchestration_checkpoint(
            checkpoint_path
        )
    )

    already_completed = bool(
        resume
        and decision_id
        and checkpoint.get(
            "last_decision_id"
        )
        == decision_id
        and checkpoint.get(
            "last_status"
        )
        == "COMPLETED"
        and checkpoint.get(
            "last_success"
        )
    )

    if errors:
        report = build_service_report(
            success=False,
            service_run_id=(
                service_run_id
            ),
            decision_id=(
                decision_id
            ),
            started_at=(
                started_at
            ),
            status="REJECTED",
            dry_run=dry_run,
            resume=resume,
            runtime=runtime,
            runtime_validation=(
                runtime_validation
            ),
            plan_validation=(
                plan_validation
            ),
            execution_report={},
            errors=errors,
        )

    elif already_completed:
        report = build_service_report(
            success=True,
            service_run_id=(
                service_run_id
            ),
            decision_id=(
                decision_id
            ),
            started_at=(
                started_at
            ),
            status=(
                "ALREADY_COMPLETED"
            ),
            dry_run=dry_run,
            resume=resume,
            runtime=runtime,
            runtime_validation=(
                runtime_validation
            ),
            plan_validation=(
                plan_validation
            ),
            execution_report={},
            errors=[],
        )

    elif dry_run:
        report = build_service_report(
            success=True,
            service_run_id=(
                service_run_id
            ),
            decision_id=(
                decision_id
            ),
            started_at=(
                started_at
            ),
            status="DRY_RUN_READY",
            dry_run=True,
            resume=resume,
            runtime=runtime,
            runtime_validation=(
                runtime_validation
            ),
            plan_validation=(
                plan_validation
            ),
            execution_report={
                "success": True,
                "status": (
                    "NOT_EXECUTED"
                ),
                "counts": {
                    "planned": (
                        plan_validation[
                            "count"
                        ]
                    ),
                    "completed": 0,
                    "failed": 0,
                    "blocked": 0,
                    "rejected": 0,
                },
                "results": [],
                "errors": [],
            },
            errors=[],
        )

    else:
        execution_report = (
            execute_orchestration_plan(
                materialized,
                project_root=root,
                policy=policy,
                process_runner=(
                    process_runner
                ),
            )
        )

        report = build_service_report(
            success=bool(
                execution_report.get(
                    "success",
                    False,
                )
            ),
            service_run_id=(
                service_run_id
            ),
            decision_id=(
                decision_id
            ),
            started_at=(
                started_at
            ),
            status=str(
                execution_report.get(
                    "status",
                    "FAILED",
                )
            ),
            dry_run=False,
            resume=resume,
            runtime=runtime,
            runtime_validation=(
                runtime_validation
            ),
            plan_validation=(
                plan_validation
            ),
            execution_report=(
                execution_report
            ),
            errors=list(
                execution_report.get(
                    "errors",
                    [],
                )
            ),
        )

    if write_outputs:
        write_orchestration_outputs(
            report,
            report_path=(
                report_path
            ),
            checkpoint_path=(
                checkpoint_path
            ),
            history_path=(
                history_path
            ),
            write_checkpoint=(
                not dry_run
                and report[
                    "status"
                ]
                not in {
                    "REJECTED",
                    "DRY_RUN_READY",
                }
            ),
        )

    return report


def build_service_report(
    *,
    success: bool,
    service_run_id: str,
    decision_id: str,
    started_at: str,
    status: str,
    dry_run: bool,
    resume: bool,
    runtime: OrchestrationRuntimeConfig,
    runtime_validation: Mapping[
        str,
        Any,
    ],
    plan_validation: Mapping[
        str,
        Any,
    ],
    execution_report: Mapping[
        str,
        Any,
    ],
    errors: list[str],
) -> dict[str, Any]:
    completed_at = datetime.now(
        UTC
    ).isoformat()

    return {
        "success": bool(
            success
        ),
        "version": (
            ORCHESTRATION_SERVICE_VERSION
        ),
        "run_id": (
            service_run_id
        ),
        "decision_id": (
            decision_id
        ),
        "started_at": (
            started_at
        ),
        "completed_at": (
            completed_at
        ),
        "status": str(
            status
        ),
        "dry_run": bool(
            dry_run
        ),
        "resume": bool(
            resume
        ),
        "runtime_configuration": (
            runtime.to_dict()
        ),
        "runtime_validation": dict(
            runtime_validation
        ),
        "plan_validation": {
            "valid": bool(
                plan_validation.get(
                    "valid",
                    False,
                )
            ),
            "count": int(
                plan_validation.get(
                    "count",
                    0,
                )
            ),
            "errors": list(
                plan_validation.get(
                    "errors",
                    [],
                )
            ),
            "rows": [
                {
                    **dict(row),
                    "command": list(
                        row.get(
                            "command",
                            (),
                        )
                    ),
                }
                for row
                in plan_validation.get(
                    "rows",
                    [],
                )
            ],
        },
        "execution_report": dict(
            execution_report
        ),
        "counts": dict(
            execution_report.get(
                "counts",
                {
                    "planned": int(
                        plan_validation.get(
                            "count",
                            0,
                        )
                    ),
                    "completed": 0,
                    "failed": 0,
                    "blocked": 0,
                    "rejected": (
                        int(
                            plan_validation.get(
                                "count",
                                0,
                            )
                        )
                        if not success
                        else 0
                    ),
                },
            )
            or {}
        ),
        "errors": list(
            errors
        ),
        "contract": {
            "autonomous_service": True,
            "dry_run_supported": True,
            "resume_supported": True,
            "allowlisted_commands_only": True,
            "arbitrary_shell_forbidden": True,
            "shell_execution": False,
            "paper_only": True,
            "submits_live_orders": False,
            "credentials_used": False,
            "live_execution": False,
        },
    }


def build_service_run_id(
    decision: Mapping[
        str,
        Any,
    ],
    *,
    runtime: OrchestrationRuntimeConfig,
    dry_run: bool,
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
        "runtime": (
            runtime.to_dict()
        ),
        "dry_run": bool(
            dry_run
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
        "ORCHESTRATION-SERVICE-"
        + digest[:24]
    )


__all__ = [
    "ORCHESTRATION_SERVICE_VERSION",
    "run_orchestration_service",
]
