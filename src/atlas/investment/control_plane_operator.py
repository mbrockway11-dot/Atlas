"""Guarded operator services for Atlas Studio.

This module is the only dashboard-facing boundary allowed to create approvals,
dispatch approved remediation, or reconcile a dispatch.

Every write operation performs fresh backend validation. The Streamlit page
never imports the approval signer, dispatcher, orchestrator, or executor.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from atlas.investment.control_plane import (
    build_system_health,
)
from atlas.investment.control_plane_approval import (
    APPROVAL_JSON,
    APPROVAL_SECRET_ENV,
    create_approval,
    load_json,
    remediation_plan_hash,
    validate_approval,
    write_approval,
)
from atlas.investment.control_plane_dispatch import (
    dispatch_approved_plan,
)
from atlas.investment.control_plane_remediation import (
    REMEDIATION_PLAN_JSON,
    build_remediation_plan,
)
from atlas.investment.control_plane_operator_audit import (
    record_operator_event,
)
from atlas.investment.dispatch_reconciliation import (
    reconcile_dispatch,
)
from atlas.investment.research_scheduler import (
    build_research_scheduler_report,
)


OPERATOR_SERVICE_VERSION = "1.0.0"


def audit_operator_action(
    *,
    action: str,
    result: str,
    operator_id: str,
    session_id: str,
    reason: str = "",
    plan_hash: str = "",
    approval_id: str = "",
    dispatch_run_id: str = "",
    job_ids=(),
    metadata=None,
) -> dict[str, Any]:
    """Record a sanitized operator-control event."""
    return record_operator_event(
        action=action,
        result=result,
        operator_id=operator_id,
        session_id=session_id,
        reason=reason,
        plan_hash=plan_hash,
        approval_id=approval_id,
        dispatch_run_id=(
            dispatch_run_id
        ),
        job_ids=job_ids,
        metadata=metadata,
    )


APPROVED_PLAN_JSON = Path(
    "output/atlas_control_plane/"
    "approved_remediation_plan.json"
)

ELIGIBLE_STATUS = "READY"

PRUNABLE_STATUSES = {
    "CURRENT",
    "DISABLED",
}

BLOCKING_STATUSES = {
    "BLOCKED",
    "FAILED",
    "MISSING",
    "STALE",
}


def build_operator_preflight(
    *,
    stored_plan_path: Path = (
        REMEDIATION_PLAN_JSON
    ),
) -> dict[str, Any]:
    """Validate freshness and compute a safe executable plan subset."""
    stored_plan = load_optional_json(
        stored_plan_path
    )

    if not stored_plan:
        return preflight_failure(
            status="PLAN_MISSING",
            reason=(
                "No stored remediation plan is available."
            ),
        )

    current_health = build_system_health()
    current_plan = build_remediation_plan(
        current_health
    )

    stored_hash = remediation_plan_hash(
        stored_plan
    )

    current_hash = remediation_plan_hash(
        current_plan
    )

    plan_fresh = bool(
        stored_hash == current_hash
    )

    schedule = load_current_schedule()

    status_by_job = {
        str(row.get("job_id", "")): str(
            row.get(
                "status",
                "UNKNOWN",
            )
        )
        for row in schedule.to_dict(
            orient="records"
        )
    }

    original_steps = [
        dict(step)
        for step in stored_plan.get(
            "execution_steps",
            [],
        )
        if isinstance(step, Mapping)
    ]

    eligible_steps: list[
        dict[str, Any]
    ] = []

    pruned_current: list[str] = []
    blocked_jobs: list[str] = []
    unknown_jobs: list[str] = []

    prefix_blocked = False

    for step in original_steps:
        job_id = str(
            step.get(
                "job_id",
                "",
            )
        )

        status = status_by_job.get(
            job_id,
            "UNKNOWN",
        )

        if status in PRUNABLE_STATUSES:
            pruned_current.append(job_id)
            continue

        if status == ELIGIBLE_STATUS:
            if prefix_blocked:
                blocked_jobs.append(job_id)
                continue

            eligible_steps.append(step)
            continue

        if status in BLOCKING_STATUSES:
            prefix_blocked = True
            blocked_jobs.append(job_id)
            continue

        prefix_blocked = True
        unknown_jobs.append(job_id)

    structural_blocked = bool(
        current_plan.get(
            "plan_status",
            ""
        )
        == "BLOCKED"
    )

    secret_present = bool(
        os.environ.get(
            APPROVAL_SECRET_ENV,
            "",
        )
    )

    effective_plan = build_effective_plan(
        stored_plan=stored_plan,
        eligible_steps=eligible_steps,
    )

    effective_hash = remediation_plan_hash(
        effective_plan
    )

    if not plan_fresh:
        status = "STALE_PLAN"
        reason = (
            "Stored remediation plan no longer matches "
            "the current canonical health state."
        )
    elif structural_blocked:
        status = "STRUCTURAL_BLOCK"
        reason = (
            "Structural errors prevent controlled execution."
        )
    elif not eligible_steps:
        status = "NO_ELIGIBLE_WORK"
        reason = (
            "No remediation jobs are currently scheduler READY."
        )
    elif not secret_present:
        status = "SECRET_MISSING"
        reason = (
            f"{APPROVAL_SECRET_ENV} is not configured "
            "for this process."
        )
    else:
        status = "READY"
        reason = (
            f"{len(eligible_steps)} scheduler-ready job(s) "
            "passed guarded approval preflight."
        )

    approval_phrase = (
        "APPROVE "
        + effective_hash[:12]
    )

    return {
        "success": status == "READY",
        "version": OPERATOR_SERVICE_VERSION,
        "status": status,
        "reason": reason,
        "plan_fresh": plan_fresh,
        "stored_plan_hash": stored_hash,
        "current_plan_hash": current_hash,
        "effective_plan_hash": effective_hash,
        "source_plan_status": str(
            stored_plan.get(
                "plan_status",
                "UNKNOWN",
            )
        ),
        "current_plan_status": str(
            current_plan.get(
                "plan_status",
                "UNKNOWN",
            )
        ),
        "secret_present": secret_present,
        "eligible_job_ids": [
            str(step["job_id"])
            for step in eligible_steps
        ],
        "eligible_steps": eligible_steps,
        "pruned_current_job_ids": (
            pruned_current
        ),
        "blocked_job_ids": blocked_jobs,
        "unknown_job_ids": unknown_jobs,
        "approval_confirmation": (
            approval_phrase
        ),
        "effective_plan": effective_plan,
        "counts": {
            "source_steps": len(
                original_steps
            ),
            "eligible_steps": len(
                eligible_steps
            ),
            "pruned_current_jobs": len(
                pruned_current
            ),
            "blocked_jobs": len(
                blocked_jobs
            ),
            "unknown_jobs": len(
                unknown_jobs
            ),
        },
    }


def create_guarded_approval(
    *,
    approved_by: str,
    confirmation: str,
    operator_id: str = "",
    session_id: str = "",
    ttl_minutes: int = 30,
    max_steps: int | None = None,
    stored_plan_path: Path = (
        REMEDIATION_PLAN_JSON
    ),
    approved_plan_path: Path = (
        APPROVED_PLAN_JSON
    ),
    approval_path: Path = APPROVAL_JSON,
) -> dict[str, Any]:
    """Create an approval only after a fresh guarded preflight."""
    preflight = build_operator_preflight(
        stored_plan_path=stored_plan_path
    )

    audit_operator_action(
        action="APPROVAL_ATTEMPTED",
        result="REQUESTED",
        operator_id=(
            operator_id
            or approved_by
        ),
        session_id=session_id,
        reason=str(
            preflight.get(
                "reason",
                "",
            )
        ),
        plan_hash=str(
            preflight.get(
                "effective_plan_hash",
                "",
            )
        ),
        job_ids=preflight.get(
            "eligible_job_ids",
            [],
        ),
        metadata={
            "preflight_status": (
                preflight.get(
                    "status",
                    "",
                )
            ),
            "eligible_steps": (
                preflight.get(
                    "counts",
                    {},
                ).get(
                    "eligible_steps",
                    0,
                )
            ),
        },
    )

    if not preflight["success"]:
        audit_operator_action(
            action="APPROVAL_REJECTED",
            result="REJECTED",
            operator_id=(
                operator_id
                or approved_by
            ),
            session_id=session_id,
            reason=str(
                preflight.get(
                    "status",
                    ""
                )
            )
            + ": "
            + str(
                preflight.get(
                    "reason",
                    "",
                )
            ),
            plan_hash=str(
                preflight.get(
                    "effective_plan_hash",
                    "",
                )
            ),
            job_ids=preflight.get(
                "eligible_job_ids",
                [],
            ),
        )
        raise ValueError(
            "Approval preflight failed: "
            + str(preflight["status"])
            + ": "
            + str(preflight["reason"])
        )

    expected = str(
        preflight[
            "approval_confirmation"
        ]
    )

    if confirmation.strip() != expected:
        audit_operator_action(
            action="APPROVAL_REJECTED",
            result="REJECTED",
            operator_id=(
                operator_id
                or approved_by
            ),
            session_id=session_id,
            reason=(
                "APPROVAL_CONFIRMATION_MISMATCH"
            ),
            plan_hash=str(
                preflight.get(
                    "effective_plan_hash",
                    "",
                )
            ),
            job_ids=preflight.get(
                "eligible_job_ids",
                [],
            ),
        )

        raise ValueError(
            "Approval confirmation mismatch. "
            f"Expected: {expected}"
        )

    if not approved_by.strip():
        raise ValueError(
            "Approved-by identity is required."
        )

    existing = load_optional_json(
        approval_path
    )

    if existing and not bool(
        existing.get(
            "used",
            False,
        )
    ):
        if not approval_is_expired(
            existing
        ):
            raise ValueError(
                "An unused, unexpired approval already exists."
            )

    effective_plan = dict(
        preflight["effective_plan"]
    )

    available_steps = len(
        effective_plan.get(
            "execution_steps",
            [],
        )
    )

    step_limit = (
        available_steps
        if max_steps is None
        else min(
            max(
                1,
                int(max_steps),
            ),
            available_steps,
        )
    )

    effective_plan[
        "execution_steps"
    ] = list(
        effective_plan[
            "execution_steps"
        ][
            :step_limit
        ]
    )

    effective_plan[
        "counts"
    ] = dict(
        effective_plan.get(
            "counts",
            {},
        )
        or {}
    )

    effective_plan[
        "counts"
    ][
        "execution_steps"
    ] = len(
        effective_plan[
            "execution_steps"
        ]
    )

    write_json_atomic(
        effective_plan,
        approved_plan_path,
    )

    approval = create_approval(
        effective_plan,
        approved_by=approved_by,
        ttl_minutes=ttl_minutes,
        max_steps=len(
            effective_plan[
                "execution_steps"
            ]
        ),
    )

    write_approval(
        approval,
        approval_path,
    )

    audit_operator_action(
        action="APPROVAL_CREATED",
        result="SUCCEEDED",
        operator_id=(
            operator_id
            or approved_by
        ),
        session_id=session_id,
        reason=(
            "Signed approval created."
        ),
        plan_hash=(
            remediation_plan_hash(
                effective_plan
            )
        ),
        approval_id=str(
            approval.get(
                "approval_id",
                "",
            )
        ),
        job_ids=approval.get(
            "approved_job_ids",
            [],
        ),
        metadata={
            "expires_at": (
                approval.get(
                    "expires_at",
                    "",
                )
            ),
            "max_steps": (
                approval.get(
                    "max_steps",
                    0,
                )
            ),
        },
    )

    return {
        "success": True,
        "approval": safe_approval_result(
            approval
        ),
        "approved_plan_path": str(
            approved_plan_path
        ),
        "effective_plan_hash": (
            remediation_plan_hash(
                effective_plan
            )
        ),
        "approved_job_ids": list(
            approval[
                "approved_job_ids"
            ]
        ),
        "preflight": without_effective_plan(
            preflight
        ),
    }


def build_dispatch_preflight(
    *,
    approved_plan_path: Path = (
        APPROVED_PLAN_JSON
    ),
    approval_path: Path = APPROVAL_JSON,
) -> dict[str, Any]:
    """Revalidate approval, expiry, hash, and scheduler eligibility."""
    plan = load_optional_json(
        approved_plan_path
    )

    approval = load_optional_json(
        approval_path
    )

    if not plan:
        return preflight_failure(
            status="APPROVED_PLAN_MISSING",
            reason=(
                "Approved plan snapshot is missing."
            ),
        )

    if not approval:
        return preflight_failure(
            status="APPROVAL_MISSING",
            reason=(
                "No approval record is available."
            ),
        )

    validation = validate_approval(
        plan=plan,
        approval=approval,
    )

    schedule = load_current_schedule()

    status_by_job = {
        str(row.get("job_id", "")): str(
            row.get(
                "status",
                "UNKNOWN",
            )
        )
        for row in schedule.to_dict(
            orient="records"
        )
    }

    approved_job_ids = [
        str(value)
        for value in approval.get(
            "approved_job_ids",
            [],
        )
    ]

    ineligible = {
        job_id: status_by_job.get(
            job_id,
            "UNKNOWN",
        )
        for job_id in approved_job_ids
        if status_by_job.get(
            job_id,
            "UNKNOWN",
        )
        != ELIGIBLE_STATUS
    }

    if not validation["valid"]:
        status = "APPROVAL_INVALID"
        reason = "|".join(
            validation["errors"]
        )
    elif ineligible:
        status = "APPROVED_SCOPE_CHANGED"
        reason = (
            "One or more approved jobs are no longer "
            "scheduler READY."
        )
    else:
        status = "READY"
        reason = (
            "Approval and current scheduler scope are valid."
        )

    confirmation = (
        "DISPATCH "
        + str(
            approval.get(
                "approval_id",
                "",
            )
        )
    )

    return {
        "success": status == "READY",
        "status": status,
        "reason": reason,
        "approval_valid": bool(
            validation["valid"]
        ),
        "approval_errors": list(
            validation["errors"]
        ),
        "approval_id": str(
            approval.get(
                "approval_id",
                "",
            )
        ),
        "approved_by": str(
            approval.get(
                "approved_by",
                "",
            )
        ),
        "approved_job_ids": (
            approved_job_ids
        ),
        "ineligible_job_statuses": (
            ineligible
        ),
        "dispatch_confirmation": (
            confirmation
        ),
        "expires_at": str(
            approval.get(
                "expires_at",
                "",
            )
        ),
        "used": bool(
            approval.get(
                "used",
                False,
            )
        ),
    }


def dispatch_guarded_approval(
    *,
    confirmation: str,
    operator_id: str = "",
    session_id: str = "",
    timeout_seconds: int = 1800,
    continue_on_failure: bool = False,
    approved_plan_path: Path = (
        APPROVED_PLAN_JSON
    ),
    approval_path: Path = APPROVAL_JSON,
) -> dict[str, Any]:
    """Dispatch only after fresh approval and scheduler validation."""
    preflight = build_dispatch_preflight(
        approved_plan_path=(
            approved_plan_path
        ),
        approval_path=approval_path,
    )

    audit_operator_action(
        action="DISPATCH_ATTEMPTED",
        result="REQUESTED",
        operator_id=(
            operator_id
            or str(
                preflight.get(
                    "approved_by",
                    "",
                )
            )
        ),
        session_id=session_id,
        reason=str(
            preflight.get(
                "reason",
                "",
            )
        ),
        approval_id=str(
            preflight.get(
                "approval_id",
                "",
            )
        ),
        job_ids=preflight.get(
            "approved_job_ids",
            [],
        ),
        metadata={
            "preflight_status": (
                preflight.get(
                    "status",
                    "",
                )
            ),
            "expires_at": (
                preflight.get(
                    "expires_at",
                    "",
                )
            ),
        },
    )

    if not preflight["success"]:
        audit_operator_action(
            action="DISPATCH_REJECTED",
            result="REJECTED",
            operator_id=(
                operator_id
                or str(
                    preflight.get(
                        "approved_by",
                        "",
                    )
                )
            ),
            session_id=session_id,
            reason=str(
                preflight.get(
                    "status",
                    "",
                )
            )
            + ": "
            + str(
                preflight.get(
                    "reason",
                    "",
                )
            ),
            approval_id=str(
                preflight.get(
                    "approval_id",
                    "",
                )
            ),
            job_ids=preflight.get(
                "approved_job_ids",
                [],
            ),
        )
        raise ValueError(
            "Dispatch preflight failed: "
            + str(preflight["status"])
            + ": "
            + str(preflight["reason"])
        )

    expected = str(
        preflight[
            "dispatch_confirmation"
        ]
    )

    if confirmation.strip() != expected:
        audit_operator_action(
            action="DISPATCH_REJECTED",
            result="REJECTED",
            operator_id=(
                operator_id
                or str(
                    preflight.get(
                        "approved_by",
                        "",
                    )
                )
            ),
            session_id=session_id,
            reason=(
                "DISPATCH_CONFIRMATION_MISMATCH"
            ),
            approval_id=str(
                preflight.get(
                    "approval_id",
                    "",
                )
            ),
            job_ids=preflight.get(
                "approved_job_ids",
                [],
            ),
        )

        raise ValueError(
            "Dispatch confirmation mismatch. "
            f"Expected: {expected}"
        )

    result = dispatch_approved_plan(
        plan_path=approved_plan_path,
        approval_path=approval_path,
        timeout_seconds=timeout_seconds,
        continue_on_failure=(
            continue_on_failure
        ),
    )

    audit_operator_action(
        action="DISPATCH_COMPLETED",
        result=(
            "SUCCEEDED"
            if result.get(
                "success",
                False,
            )
            else "FAILED"
        ),
        operator_id=(
            operator_id
            or str(
                result.get(
                    "approved_by",
                    "",
                )
            )
        ),
        session_id=session_id,
        reason=(
            "Controlled dispatch completed."
            if result.get(
                "success",
                False,
            )
            else "Controlled dispatch reported failure."
        ),
        approval_id=str(
            result.get(
                "approval_id",
                "",
            )
        ),
        dispatch_run_id=str(
            result.get(
                "run_id",
                "",
            )
        ),
        job_ids=result.get(
            "approved_job_ids",
            [],
        ),
    )

    return {
        "success": bool(
            result.get(
                "success",
                False,
            )
        ),
        "approval_id": str(
            result.get(
                "approval_id",
                "",
            )
        ),
        "approved_by": str(
            result.get(
                "approved_by",
                "",
            )
        ),
        "approved_job_ids": list(
            result.get(
                "approved_job_ids",
                [],
            )
        ),
        "run_id": str(
            result.get(
                "run_id",
                "",
            )
        ),
        "cycle": dict(
            result.get(
                "cycle",
                {},
            )
            or {}
        ),
        "preflight": preflight,
    }


def reconcile_guarded_dispatch(
    *,
    operator_id: str = "",
    session_id: str = "",
    approved_plan_path: Path = (
        APPROVED_PLAN_JSON
    ),
    approval_path: Path = APPROVAL_JSON,
) -> dict[str, Any]:
    """Reconcile the latest guarded dispatch without executing more work."""
    approval = load_optional_json(
        approval_path
    )

    audit_operator_action(
        action="RECONCILIATION_ATTEMPTED",
        result="REQUESTED",
        operator_id=(
            operator_id
            or str(
                approval.get(
                    "approved_by",
                    "",
                )
            )
        ),
        session_id=session_id,
        reason=(
            "Operator requested reconciliation."
        ),
        approval_id=str(
            approval.get(
                "approval_id",
                "",
            )
        ),
        dispatch_run_id=str(
            approval.get(
                "dispatch_run_id",
                "",
            )
        ),
        job_ids=approval.get(
            "approved_job_ids",
            [],
        ),
    )

    if not approval:
        audit_operator_action(
            action="RECONCILIATION_REJECTED",
            result="REJECTED",
            operator_id=operator_id,
            session_id=session_id,
            reason="APPROVAL_MISSING",
        )

        raise ValueError(
            "No approval record is available."
        )

    if not bool(
        approval.get(
            "used",
            False,
        )
    ):
        audit_operator_action(
            action="RECONCILIATION_REJECTED",
            result="REJECTED",
            operator_id=(
                operator_id
                or str(
                    approval.get(
                        "approved_by",
                        "",
                    )
                )
            ),
            session_id=session_id,
            reason=(
                "APPROVAL_NOT_DISPATCHED"
            ),
            approval_id=str(
                approval.get(
                    "approval_id",
                    "",
                )
            ),
            job_ids=approval.get(
                "approved_job_ids",
                [],
            ),
        )

        raise ValueError(
            "Approval has not been dispatched."
        )

    report = reconcile_dispatch(
        approval_path=approval_path,
        original_plan_path=(
            approved_plan_path
        ),
    )

    audit_operator_action(
        action="RECONCILIATION_COMPLETED",
        result=(
            "SUCCEEDED"
            if report.get(
                "success",
                False,
            )
            else "FAILED"
        ),
        operator_id=(
            operator_id
            or str(
                approval.get(
                    "approved_by",
                    "",
                )
            )
        ),
        session_id=session_id,
        reason=str(
            report.get(
                "outcome",
                "UNKNOWN",
            )
        ),
        approval_id=str(
            approval.get(
                "approval_id",
                "",
            )
        ),
        dispatch_run_id=str(
            approval.get(
                "dispatch_run_id",
                "",
            )
        ),
        job_ids=approval.get(
            "approved_job_ids",
            [],
        ),
        metadata={
            "outcome": report.get(
                "outcome",
                "UNKNOWN",
            ),
            "scope_valid": (
                report.get(
                    "receipt",
                    {},
                ).get(
                    "scope_valid",
                    False,
                )
            ),
        },
    )

    return report


def build_effective_plan(
    *,
    stored_plan: Mapping[str, Any],
    eligible_steps: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:
    plan = json.loads(
        json.dumps(
            dict(stored_plan),
            default=str,
        )
    )

    plan[
        "execution_steps"
    ] = eligible_steps

    plan["counts"] = dict(
        plan.get(
            "counts",
            {},
        )
        or {}
    )

    plan["counts"][
        "execution_steps"
    ] = len(
        eligible_steps
    )

    plan["counts"][
        "pruned_by_operator_preflight"
    ] = (
        safe_int(
            plan["counts"].get(
                "source_steps",
                0,
            )
        )
        - len(eligible_steps)
    )

    plan["operator_preflight"] = {
        "generated_at": (
            datetime.now(UTC).isoformat()
        ),
        "scheduler_ready_only": True,
        "already_current_pruned": True,
        "execution_authorized": False,
    }

    return plan


def load_current_schedule() -> pd.DataFrame:
    report = (
        build_research_scheduler_report()
    )

    outputs = report.get(
        "outputs",
        {},
    )

    if not isinstance(
        outputs,
        Mapping,
    ):
        return pd.DataFrame()

    path_text = str(
        outputs.get(
            "research_schedule_csv",
            "",
        )
    )

    if not path_text:
        return pd.DataFrame()

    path = Path(path_text)

    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except (
        OSError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
    ):
        return pd.DataFrame()


def approval_is_expired(
    approval: Mapping[str, Any],
) -> bool:
    try:
        expires_at = datetime.fromisoformat(
            str(
                approval.get(
                    "expires_at",
                    "",
                )
            ).replace(
                "Z",
                "+00:00",
            )
        )
    except ValueError:
        return True

    return datetime.now(
        UTC
    ) >= expires_at


def safe_approval_result(
    approval: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "approval_id": str(
            approval.get(
                "approval_id",
                "",
            )
        ),
        "approved_by": str(
            approval.get(
                "approved_by",
                "",
            )
        ),
        "approved_at": str(
            approval.get(
                "approved_at",
                "",
            )
        ),
        "expires_at": str(
            approval.get(
                "expires_at",
                "",
            )
        ),
        "approved_job_ids": [
            str(value)
            for value in approval.get(
                "approved_job_ids",
                [],
            )
        ],
        "max_steps": safe_int(
            approval.get(
                "max_steps",
                0,
            )
        ),
        "used": bool(
            approval.get(
                "used",
                False,
            )
        ),
    }


def load_optional_json(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}

    return (
        payload
        if isinstance(payload, dict)
        else {}
    )


def write_json_atomic(
    payload: Mapping[str, Any],
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            dict(payload),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)


def preflight_failure(
    *,
    status: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "success": False,
        "version": (
            OPERATOR_SERVICE_VERSION
        ),
        "status": status,
        "reason": reason,
        "plan_fresh": False,
        "secret_present": bool(
            os.environ.get(
                APPROVAL_SECRET_ENV,
                "",
            )
        ),
        "eligible_job_ids": [],
        "eligible_steps": [],
        "pruned_current_job_ids": [],
        "blocked_job_ids": [],
        "unknown_job_ids": [],
        "approval_confirmation": "",
        "counts": {
            "source_steps": 0,
            "eligible_steps": 0,
            "pruned_current_jobs": 0,
            "blocked_jobs": 0,
            "unknown_jobs": 0,
        },
    }


def without_effective_plan(
    preflight: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        key: value
        for key, value in preflight.items()
        if key != "effective_plan"
    }


def safe_int(
    value: Any,
) -> int:
    try:
        return int(value)
    except (
        TypeError,
        ValueError,
    ):
        return 0


__all__ = [
    "APPROVED_PLAN_JSON",
    "OPERATOR_SERVICE_VERSION",
    "build_dispatch_preflight",
    "build_operator_preflight",
    "create_guarded_approval",
    "dispatch_guarded_approval",
    "reconcile_guarded_dispatch",
]
