"""Verified self-healing support for the Atlas research orchestrator.

The scheduler remains the only owner of artifact health and dependency state.
This module only interprets scheduler output after execution attempts.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from atlas.investment.artifact_contracts import (
    validate_job_outputs,
)


HEALTHY_STATUSES = {
    "CURRENT",
}

UNHEALTHY_STATUSES = {
    "READY",
    "BLOCKED",
    "FAILED",
    "MISSING",
    "STALE",
}

RETRYABLE_RESULT_STATUSES = {
    "FAILED",
    "TIMED_OUT",
    "RECOVERY_FAILED",
}


def find_job_row(
    schedule: pd.DataFrame,
    job_id: str,
) -> dict[str, Any]:
    """Return one scheduler row as a plain mapping."""
    if schedule is None or schedule.empty:
        return {}

    matches = schedule[
        schedule[
            "job_id"
        ].astype(str).eq(
            str(job_id)
        )
    ]

    if matches.empty:
        return {}

    return dict(
        matches.iloc[0].to_dict()
    )


def verify_job_health(
    schedule: pd.DataFrame,
    job_id: str,
) -> dict[str, Any]:
    """Verify whether an executed job repaired its canonical artifact."""
    row = find_job_row(
        schedule,
        job_id,
    )

    if not row:
        return {
            "job_id": str(job_id),
            "verified": False,
            "healed": False,
            "status": "UNKNOWN",
            "reason": (
                "Job was absent from refreshed "
                "scheduler output."
            ),
        }

    status = str(
        row.get(
            "status",
            "UNKNOWN",
        )
    )

    output_contract = validate_job_outputs(
        str(job_id)
    )

    scheduler_healthy = (
        status in HEALTHY_STATUSES
    )

    contract_healthy = bool(
        output_contract["success"]
    )

    return {
        "job_id": str(job_id),
        "verified": True,
        "healed": bool(
            scheduler_healthy
            and contract_healthy
        ),
        "scheduler_healthy": (
            scheduler_healthy
        ),
        "contract_healthy": (
            contract_healthy
        ),
        "status": status,
        "reason": str(
            row.get(
                "reason",
                "",
            )
        ),
        "exists": bool(
            row.get(
                "exists",
                False,
            )
        ),
        "valid": bool(
            row.get(
                "valid",
                False,
            )
        ),
        "fresh": bool(
            row.get(
                "fresh",
                False,
            )
        ),
        "dirty": bool(
            row.get(
                "dirty",
                False,
            )
        ),
        "content_stale": bool(
            row.get(
                "content_stale",
                False,
            )
        ),
        "invalidation_reason": str(
            row.get(
                "invalidation_reason",
                "",
            )
        ),
        "required_output_count": int(
            output_contract[
                "required_output_count"
            ]
        ),
        "valid_required_output_count": int(
            output_contract[
                "valid_required_output_count"
            ]
        ),
        "missing_or_invalid_required_count": int(
            output_contract[
                "missing_or_invalid_required_count"
            ]
        ),
        "required_output_failures": list(
            output_contract[
                "required_failures"
            ]
        ),
    }


def can_retry(
    *,
    attempts: int,
    max_recovery_attempts: int,
    self_heal: bool,
) -> bool:
    """Return whether another bounded healing attempt is allowed."""
    return bool(
        self_heal
        and int(attempts)
        < max(
            1,
            int(max_recovery_attempts),
        )
    )


def annotate_recovery_result(
    result: dict[str, Any],
    *,
    attempt: int,
    verification: dict[str, Any],
    retry_pending: bool,
    self_heal: bool,
) -> dict[str, Any]:
    """Attach self-healing metadata to one execution result."""
    enriched = dict(result)

    enriched.update({
        "self_healing_enabled": bool(
            self_heal
        ),
        "recovery_attempt": int(
            attempt
        ),
        "artifact_verified": bool(
            verification.get(
                "verified",
                False,
            )
        ),
        "artifact_healed": bool(
            verification.get(
                "healed",
                False,
            )
        ),
        "post_execution_status": str(
            verification.get(
                "status",
                "UNKNOWN",
            )
        ),
        "post_execution_reason": str(
            verification.get(
                "reason",
                "",
            )
        ),
        "scheduler_healthy": bool(
            verification.get(
                "scheduler_healthy",
                False,
            )
        ),
        "contract_healthy": bool(
            verification.get(
                "contract_healthy",
                False,
            )
        ),
        "required_output_count": int(
            verification.get(
                "required_output_count",
                0,
            )
        ),
        "valid_required_output_count": int(
            verification.get(
                "valid_required_output_count",
                0,
            )
        ),
        "missing_or_invalid_required_count": int(
            verification.get(
                "missing_or_invalid_required_count",
                0,
            )
        ),
        "required_output_failures": list(
            verification.get(
                "required_output_failures",
                [],
            )
        ),
        "retry_pending": bool(
            retry_pending
        ),
    })

    return enriched


def schedule_signature(
    schedule: pd.DataFrame,
) -> tuple[tuple[str, str], ...]:
    """Build a deterministic health signature for no-progress detection."""
    if schedule is None or schedule.empty:
        return ()

    pairs = [
        (
            str(row.get("job_id", "")),
            str(row.get("status", "")),
        )
        for row in schedule.to_dict(
            orient="records"
        )
    ]

    return tuple(
        sorted(pairs)
    )


def blocked_job_ids(
    schedule: pd.DataFrame,
) -> list[str]:
    """Return all currently blocked jobs."""
    if schedule is None or schedule.empty:
        return []

    return schedule[
        schedule[
            "status"
        ].astype(str).eq(
            "BLOCKED"
        )
    ][
        "job_id"
    ].astype(str).tolist()


__all__ = [
    "HEALTHY_STATUSES",
    "RETRYABLE_RESULT_STATUSES",
    "UNHEALTHY_STATUSES",
    "annotate_recovery_result",
    "blocked_job_ids",
    "can_retry",
    "find_job_row",
    "schedule_signature",
    "verify_job_health",
]
