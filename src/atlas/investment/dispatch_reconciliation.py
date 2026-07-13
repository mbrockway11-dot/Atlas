"""Post-dispatch reconciliation for the Atlas Control Plane.

The reconciliation layer is read-only after dispatch. It connects:

- the consumed signed approval;
- the approved remediation-plan hash;
- immutable execution provenance;
- the orchestrator run;
- post-dispatch system health;
- the newly generated remediation plan.

It verifies that only approved jobs were attempted and records whether the
approved repair scope was completed, partially repaired, unchanged, violated,
or failed.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

from atlas.investment.control_plane import (
    build_and_write_system_health,
)
from atlas.investment.control_plane_approval import (
    APPROVAL_JSON,
    REMEDIATION_PLAN_JSON,
    load_json,
    remediation_plan_hash,
)
from atlas.investment.control_plane_remediation import (
    build_and_write_remediation_plan,
)
from atlas.investment.research_orchestrator.provenance import (
    read_provenance_events,
)


RECONCILIATION_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/atlas_control_plane"
)

DISPATCH_RECEIPTS_JSONL = (
    OUTPUT_DIR
    / "dispatch_receipts.jsonl"
)

RECONCILIATION_JSON = (
    OUTPUT_DIR
    / "dispatch_reconciliation.json"
)

RECONCILIATION_CSV = (
    OUTPUT_DIR
    / "dispatch_reconciliation.csv"
)

RECONCILIATION_MD = (
    OUTPUT_DIR
    / "dispatch_reconciliation.md"
)


SUCCESS_STATUSES = {
    "SUCCEEDED",
    "CACHED",
}

FAILURE_STATUSES = {
    "FAILED",
    "TIMED_OUT",
    "RECOVERY_FAILED",
}

ATTEMPT_STATUSES = (
    SUCCESS_STATUSES
    | FAILURE_STATUSES
    | {
        "RETRY_PENDING",
    }
)


def reconcile_dispatch(
    *,
    approval_path: Path = APPROVAL_JSON,
    original_plan_path: Path = REMEDIATION_PLAN_JSON,
    receipt_path: Path = DISPATCH_RECEIPTS_JSONL,
) -> dict[str, Any]:
    """Reconcile one consumed approval against provenance and current health."""
    reconciled_at = (
        datetime.now(UTC).isoformat()
    )

    approval = load_json(
        approval_path
    )

    original_plan = load_json(
        original_plan_path
    )

    approved_job_ids = [
        str(value)
        for value in approval.get(
            "approved_job_ids",
            [],
        )
    ]

    approval_id = str(
        approval.get(
            "approval_id",
            "",
        )
    )

    dispatch_run_id = str(
        approval.get(
            "dispatch_run_id",
            "",
        )
    )

    stored_plan_hash = str(
        approval.get(
            "plan_hash",
            "",
        )
    )

    current_plan_hash = (
        remediation_plan_hash(
            original_plan
        )
    )

    provenance_events = (
        read_provenance_events()
    )

    run_events = select_run_events(
        provenance_events,
        dispatch_run_id,
    )

    attempted_job_ids = ordered_unique(
        str(
            event.get(
                "job_id",
                "",
            )
        )
        for event in run_events
        if str(
            event.get(
                "status",
                "",
            )
        )
        in ATTEMPT_STATUSES
    )

    successful_job_ids = ordered_unique(
        str(
            event.get(
                "job_id",
                "",
            )
        )
        for event in run_events
        if str(
            event.get(
                "status",
                "",
            )
        )
        in SUCCESS_STATUSES
    )

    failed_job_ids = ordered_unique(
        str(
            event.get(
                "job_id",
                "",
            )
        )
        for event in run_events
        if str(
            event.get(
                "status",
                "",
            )
        )
        in FAILURE_STATUSES
    )

    unapproved_job_ids = [
        job_id
        for job_id in attempted_job_ids
        if job_id not in approved_job_ids
    ]

    approved_but_unattempted = [
        job_id
        for job_id in approved_job_ids
        if job_id not in attempted_job_ids
    ]

    approved_successful = [
        job_id
        for job_id in approved_job_ids
        if job_id in successful_job_ids
    ]

    approval_consumed = bool(
        approval.get(
            "used",
            False,
        )
    )

    approval_linked = bool(
        approval_consumed
        and dispatch_run_id
    )

    plan_hash_matches = bool(
        stored_plan_hash
        == current_plan_hash
    )

    post_health = (
        build_and_write_system_health()
    )

    next_plan = (
        build_and_write_remediation_plan(
            post_health
        )
    )

    original_counts = dict(
        original_plan.get(
            "counts",
            {},
        )
        or {}
    )

    next_counts = dict(
        next_plan.get(
            "counts",
            {},
        )
        or {}
    )

    original_step_count = safe_int(
        original_counts.get(
            "execution_steps",
            len(
                original_plan.get(
                    "execution_steps",
                    [],
                )
                or []
            ),
        )
    )

    next_step_count = safe_int(
        next_counts.get(
            "execution_steps",
            len(
                next_plan.get(
                    "execution_steps",
                    [],
                )
                or []
            ),
        )
    )

    original_recommendation_count = (
        safe_int(
            original_counts.get(
                "source_recommendations",
                0,
            )
        )
    )

    next_recommendation_count = (
        safe_int(
            next_counts.get(
                "source_recommendations",
                0,
            )
        )
    )

    step_delta = (
        original_step_count
        - next_step_count
    )

    recommendation_delta = (
        original_recommendation_count
        - next_recommendation_count
    )

    repaired_job_ids = determine_repaired_jobs(
        approved_job_ids=(
            approved_job_ids
        ),
        successful_job_ids=(
            successful_job_ids
        ),
        next_plan=next_plan,
    )

    unresolved_approved_job_ids = [
        job_id
        for job_id in approved_job_ids
        if job_id not in repaired_job_ids
    ]

    outcome = classify_outcome(
        approval_linked=approval_linked,
        plan_hash_matches=(
            plan_hash_matches
        ),
        approved_job_ids=(
            approved_job_ids
        ),
        attempted_job_ids=(
            attempted_job_ids
        ),
        approved_successful=(
            approved_successful
        ),
        failed_job_ids=(
            failed_job_ids
        ),
        unapproved_job_ids=(
            unapproved_job_ids
        ),
        repaired_job_ids=(
            repaired_job_ids
        ),
        unresolved_approved_job_ids=(
            unresolved_approved_job_ids
        ),
        step_delta=step_delta,
        recommendation_delta=(
            recommendation_delta
        ),
    )

    receipt = {
        "version": (
            RECONCILIATION_VERSION
        ),
        "receipt_id": build_receipt_id(
            approval_id=approval_id,
            run_id=dispatch_run_id,
            reconciled_at=(
                reconciled_at
            ),
        ),
        "reconciled_at": (
            reconciled_at
        ),
        "approval_id": approval_id,
        "approved_by": str(
            approval.get(
                "approved_by",
                "",
            )
        ),
        "approval_used": (
            approval_consumed
        ),
        "approval_used_at": str(
            approval.get(
                "used_at",
                "",
            )
        ),
        "dispatch_run_id": (
            dispatch_run_id
        ),
        "plan_hash": (
            stored_plan_hash
        ),
        "plan_hash_matches": (
            plan_hash_matches
        ),
        "approved_job_ids": (
            approved_job_ids
        ),
        "attempted_job_ids": (
            attempted_job_ids
        ),
        "successful_job_ids": (
            successful_job_ids
        ),
        "failed_job_ids": (
            failed_job_ids
        ),
        "unapproved_job_ids": (
            unapproved_job_ids
        ),
        "approved_but_unattempted": (
            approved_but_unattempted
        ),
        "repaired_job_ids": (
            repaired_job_ids
        ),
        "unresolved_approved_job_ids": (
            unresolved_approved_job_ids
        ),
        "outcome": outcome,
        "scope_valid": not bool(
            unapproved_job_ids
        ),
        "provenance_event_count": (
            len(run_events)
        ),
        "before": {
            "health_status": str(
                original_plan.get(
                    "source_health_status",
                    "UNKNOWN",
                )
            ),
            "recommendation_count": (
                original_recommendation_count
            ),
            "execution_step_count": (
                original_step_count
            ),
        },
        "after": {
            "health_status": str(
                post_health.get(
                    "overall_status",
                    "UNKNOWN",
                )
            ),
            "recommendation_count": (
                next_recommendation_count
            ),
            "execution_step_count": (
                next_step_count
            ),
            "next_plan_status": str(
                next_plan.get(
                    "plan_status",
                    "UNKNOWN",
                )
            ),
        },
        "delta": {
            "recommendations_resolved": (
                recommendation_delta
            ),
            "execution_steps_reduced": (
                step_delta
            ),
        },
    }

    append_dispatch_receipt(
        receipt,
        receipt_path=receipt_path,
    )

    report = {
        "success": outcome
        not in {
            "FAILED",
            "SCOPE_VIOLATION",
        },
        "version": (
            RECONCILIATION_VERSION
        ),
        "generated_at": (
            reconciled_at
        ),
        "outcome": outcome,
        "summary": build_summary(
            receipt
        ),
        "receipt": receipt,
        "post_dispatch_health": {
            "overall_status": str(
                post_health.get(
                    "overall_status",
                    "UNKNOWN",
                )
            ),
            "counts": dict(
                post_health.get(
                    "counts",
                    {},
                )
                or {}
            ),
        },
        "next_remediation": {
            "plan_status": str(
                next_plan.get(
                    "plan_status",
                    "UNKNOWN",
                )
            ),
            "execution": dict(
                next_plan.get(
                    "execution",
                    {},
                )
                or {}
            ),
            "counts": dict(
                next_plan.get(
                    "counts",
                    {},
                )
                or {}
            ),
        },
        "contract": {
            "read_only": True,
            "dispatches_jobs": False,
            "verifies_approval_scope": True,
            "verifies_plan_hash": True,
            "uses_immutable_provenance": True,
            "rebuilds_control_plane": True,
            "rebuilds_remediation_plan": True,
        },
        "outputs": {
            "dispatch_receipts_jsonl": str(
                DISPATCH_RECEIPTS_JSONL
            ),
            "reconciliation_json": str(
                RECONCILIATION_JSON
            ),
            "reconciliation_csv": str(
                RECONCILIATION_CSV
            ),
            "reconciliation_markdown": str(
                RECONCILIATION_MD
            ),
        },
    }

    write_reconciliation_outputs(
        report
    )

    return report


def classify_outcome(
    *,
    approval_linked: bool,
    plan_hash_matches: bool,
    approved_job_ids: list[str],
    attempted_job_ids: list[str],
    approved_successful: list[str],
    failed_job_ids: list[str],
    unapproved_job_ids: list[str],
    repaired_job_ids: list[str],
    unresolved_approved_job_ids: list[str],
    step_delta: int,
    recommendation_delta: int,
) -> str:
    """Classify one controlled dispatch reconciliation outcome."""
    if (
        not approval_linked
        or not plan_hash_matches
    ):
        return "FAILED"

    if unapproved_job_ids:
        return "SCOPE_VIOLATION"

    if failed_job_ids:
        return "FAILED"

    if (
        approved_job_ids
        and set(approved_job_ids)
        .issubset(
            set(repaired_job_ids)
        )
        and set(approved_job_ids)
        .issubset(
            set(approved_successful)
        )
    ):
        return "RECONCILED"

    made_progress = bool(
        repaired_job_ids
        or approved_successful
        or step_delta > 0
        or recommendation_delta > 0
    )

    if (
        made_progress
        and unresolved_approved_job_ids
    ):
        return "PARTIALLY_REPAIRED"

    if not attempted_job_ids:
        return "NO_PROGRESS"

    if not made_progress:
        return "NO_PROGRESS"

    return "FAILED"


def determine_repaired_jobs(
    *,
    approved_job_ids: list[str],
    successful_job_ids: list[str],
    next_plan: Mapping[str, Any],
) -> list[str]:
    """Identify approved jobs no longer present in the next repair plan."""
    remaining = {
        str(
            item.get(
                "job_id",
                "",
            )
        )
        for item in next_plan.get(
            "execution_steps",
            [],
        )
        if isinstance(item, Mapping)
    }

    return [
        job_id
        for job_id in approved_job_ids
        if (
            job_id in successful_job_ids
            and job_id not in remaining
        )
    ]


def select_run_events(
    events: Iterable[
        Mapping[str, Any]
    ],
    run_id: str,
) -> list[dict[str, Any]]:
    """Select provenance events belonging to one dispatch run."""
    return [
        dict(event)
        for event in events
        if str(
            event.get(
                "run_id",
                "",
            )
        )
        == str(run_id)
    ]


def append_dispatch_receipt(
    receipt: Mapping[str, Any],
    *,
    receipt_path: Path = (
        DISPATCH_RECEIPTS_JSONL
    ),
) -> None:
    """Append one immutable dispatch receipt, avoiding duplicate IDs."""
    receipt_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing_ids = {
        str(
            item.get(
                "receipt_id",
                "",
            )
        )
        for item in read_dispatch_receipts(
            receipt_path
        )
    }

    receipt_id = str(
        receipt.get(
            "receipt_id",
            "",
        )
    )

    if receipt_id in existing_ids:
        return

    with receipt_path.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(
            json.dumps(
                dict(receipt),
                sort_keys=True,
                ensure_ascii=False,
                default=str,
            )
            + "\n"
        )


def read_dispatch_receipts(
    path: Path = DISPATCH_RECEIPTS_JSONL,
) -> list[dict[str, Any]]:
    """Read valid immutable dispatch receipts."""
    if not path.exists():
        return []

    receipts: list[
        dict[str, Any]
    ] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        for line in handle:
            text = line.strip()

            if not text:
                continue

            try:
                payload = json.loads(
                    text
                )
            except json.JSONDecodeError:
                continue

            if isinstance(payload, dict):
                receipts.append(payload)

    return receipts


def build_receipt_id(
    *,
    approval_id: str,
    run_id: str,
    reconciled_at: str = "",
) -> str:
    """Build one stable receipt ID per approval and dispatch run.

    ``reconciled_at`` remains accepted for backward compatibility but is not
    part of the identity. Re-running reconciliation therefore cannot append
    duplicate receipts for the same controlled dispatch.
    """
    payload = {
        "approval_id": approval_id,
        "run_id": run_id,
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return (
        "RECEIPT-"
        + hashlib.sha256(
            encoded
        ).hexdigest()[:24]
    )


def write_reconciliation_outputs(
    report: Mapping[str, Any],
) -> None:
    """Write reconciliation JSON, CSV, and Markdown outputs."""
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    RECONCILIATION_JSON.write_text(
        json.dumps(
            dict(report),
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    receipt = dict(
        report.get(
            "receipt",
            {},
        )
        or {}
    )

    rows = []

    approved = list(
        receipt.get(
            "approved_job_ids",
            [],
        )
        or []
    )

    attempted = set(
        receipt.get(
            "attempted_job_ids",
            [],
        )
        or []
    )

    successful = set(
        receipt.get(
            "successful_job_ids",
            [],
        )
        or []
    )

    failed = set(
        receipt.get(
            "failed_job_ids",
            [],
        )
        or []
    )

    repaired = set(
        receipt.get(
            "repaired_job_ids",
            [],
        )
        or []
    )

    for job_id in approved:
        rows.append({
            "approval_id": receipt.get(
                "approval_id",
                "",
            ),
            "dispatch_run_id": receipt.get(
                "dispatch_run_id",
                "",
            ),
            "outcome": receipt.get(
                "outcome",
                "",
            ),
            "job_id": job_id,
            "approved": True,
            "attempted": (
                job_id in attempted
            ),
            "successful": (
                job_id in successful
            ),
            "failed": (
                job_id in failed
            ),
            "repaired": (
                job_id in repaired
            ),
        })

    for job_id in receipt.get(
        "unapproved_job_ids",
        [],
    ):
        rows.append({
            "approval_id": receipt.get(
                "approval_id",
                "",
            ),
            "dispatch_run_id": receipt.get(
                "dispatch_run_id",
                "",
            ),
            "outcome": receipt.get(
                "outcome",
                "",
            ),
            "job_id": job_id,
            "approved": False,
            "attempted": True,
            "successful": (
                job_id in successful
            ),
            "failed": (
                job_id in failed
            ),
            "repaired": False,
        })

    pd.DataFrame(
        rows
    ).to_csv(
        RECONCILIATION_CSV,
        index=False,
    )

    RECONCILIATION_MD.write_text(
        render_reconciliation_markdown(
            report
        ),
        encoding="utf-8",
    )


def render_reconciliation_markdown(
    report: Mapping[str, Any],
) -> str:
    receipt = dict(
        report.get(
            "receipt",
            {},
        )
        or {}
    )

    before = dict(
        receipt.get(
            "before",
            {},
        )
        or {}
    )

    after = dict(
        receipt.get(
            "after",
            {},
        )
        or {}
    )

    delta = dict(
        receipt.get(
            "delta",
            {},
        )
        or {}
    )

    lines = [
        "# Atlas Dispatch Reconciliation",
        "",
        (
            f"- Outcome: "
            f"`{report.get('outcome', '')}`"
        ),
        (
            f"- Approval ID: "
            f"`{receipt.get('approval_id', '')}`"
        ),
        (
            f"- Dispatch run: "
            f"`{receipt.get('dispatch_run_id', '')}`"
        ),
        (
            f"- Scope valid: "
            f"`{receipt.get('scope_valid', False)}`"
        ),
        (
            f"- Plan hash valid: "
            f"`{receipt.get('plan_hash_matches', False)}`"
        ),
        "",
        "## Health Change",
        "",
        (
            f"- Before: "
            f"`{before.get('health_status', '')}`"
        ),
        (
            f"- After: "
            f"`{after.get('health_status', '')}`"
        ),
        (
            f"- Recommendations resolved: "
            f"`{delta.get('recommendations_resolved', 0)}`"
        ),
        (
            f"- Execution steps reduced: "
            f"`{delta.get('execution_steps_reduced', 0)}`"
        ),
        "",
        "## Approved Scope",
        "",
        "| Job | Attempted | Successful | Repaired |",
        "|---|---:|---:|---:|",
    ]

    attempted = set(
        receipt.get(
            "attempted_job_ids",
            [],
        )
        or []
    )

    successful = set(
        receipt.get(
            "successful_job_ids",
            [],
        )
        or []
    )

    repaired = set(
        receipt.get(
            "repaired_job_ids",
            [],
        )
        or []
    )

    for job_id in receipt.get(
        "approved_job_ids",
        [],
    ):
        lines.append(
            "| "
            + str(job_id)
            + " | "
            + str(
                job_id in attempted
            )
            + " | "
            + str(
                job_id in successful
            )
            + " | "
            + str(
                job_id in repaired
            )
            + " |"
        )

    if receipt.get(
        "unapproved_job_ids",
        [],
    ):
        lines.extend([
            "",
            "## Scope Violations",
            "",
        ])

        for job_id in receipt[
            "unapproved_job_ids"
        ]:
            lines.append(
                f"- `{job_id}`"
            )

    lines.append("")

    return "\n".join(lines)


def build_summary(
    receipt: Mapping[str, Any],
) -> str:
    return (
        "Atlas reconciled approval "
        f"{receipt.get('approval_id', '')} "
        f"against run "
        f"{receipt.get('dispatch_run_id', '')}: "
        f"{len(receipt.get('approved_job_ids', []))} "
        "approved job(s), "
        f"{len(receipt.get('attempted_job_ids', []))} "
        "attempted, "
        f"{len(receipt.get('repaired_job_ids', []))} "
        "repaired, and "
        f"{len(receipt.get('unapproved_job_ids', []))} "
        "scope violation(s). "
        f"Outcome: {receipt.get('outcome', '')}."
    )


def ordered_unique(
    values: Iterable[str],
) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        text = str(value)

        if not text or text in seen:
            continue

        seen.add(text)
        result.append(text)

    return result


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
    "DISPATCH_RECEIPTS_JSONL",
    "RECONCILIATION_CSV",
    "RECONCILIATION_JSON",
    "RECONCILIATION_MD",
    "RECONCILIATION_VERSION",
    "append_dispatch_receipt",
    "build_receipt_id",
    "classify_outcome",
    "determine_repaired_jobs",
    "read_dispatch_receipts",
    "reconcile_dispatch",
    "render_reconciliation_markdown",
    "select_run_events",
    "write_reconciliation_outputs",
]
