"""Tests for Phase E.4 dispatch reconciliation."""

from __future__ import annotations

from pathlib import Path

from atlas.investment import (
    dispatch_reconciliation,
)


def test_scope_violation_takes_precedence():
    outcome = (
        dispatch_reconciliation
        .classify_outcome(
            approval_linked=True,
            plan_hash_matches=True,
            approved_job_ids=[
                "alpha_engines",
            ],
            attempted_job_ids=[
                "alpha_engines",
                "macro_intelligence",
            ],
            approved_successful=[
                "alpha_engines",
            ],
            failed_job_ids=[],
            unapproved_job_ids=[
                "macro_intelligence",
            ],
            repaired_job_ids=[
                "alpha_engines",
            ],
            unresolved_approved_job_ids=[],
            step_delta=1,
            recommendation_delta=1,
        )
    )

    assert outcome == (
        "SCOPE_VIOLATION"
    )


def test_failed_event_is_failed_outcome():
    outcome = (
        dispatch_reconciliation
        .classify_outcome(
            approval_linked=True,
            plan_hash_matches=True,
            approved_job_ids=[
                "alpha_engines",
            ],
            attempted_job_ids=[
                "alpha_engines",
            ],
            approved_successful=[],
            failed_job_ids=[
                "alpha_engines",
            ],
            unapproved_job_ids=[],
            repaired_job_ids=[],
            unresolved_approved_job_ids=[
                "alpha_engines",
            ],
            step_delta=0,
            recommendation_delta=0,
        )
    )

    assert outcome == "FAILED"


def test_all_approved_repaired_is_reconciled():
    outcome = (
        dispatch_reconciliation
        .classify_outcome(
            approval_linked=True,
            plan_hash_matches=True,
            approved_job_ids=[
                "alpha_engines",
            ],
            attempted_job_ids=[
                "alpha_engines",
            ],
            approved_successful=[
                "alpha_engines",
            ],
            failed_job_ids=[],
            unapproved_job_ids=[],
            repaired_job_ids=[
                "alpha_engines",
            ],
            unresolved_approved_job_ids=[],
            step_delta=1,
            recommendation_delta=1,
        )
    )

    assert outcome == "RECONCILED"


def test_success_without_closure_is_partial():
    outcome = (
        dispatch_reconciliation
        .classify_outcome(
            approval_linked=True,
            plan_hash_matches=True,
            approved_job_ids=[
                "alpha_engines",
                "regime_intelligence",
            ],
            attempted_job_ids=[
                "alpha_engines",
            ],
            approved_successful=[
                "alpha_engines",
            ],
            failed_job_ids=[],
            unapproved_job_ids=[],
            repaired_job_ids=[
                "alpha_engines",
            ],
            unresolved_approved_job_ids=[
                "regime_intelligence",
            ],
            step_delta=1,
            recommendation_delta=0,
        )
    )

    assert outcome == (
        "PARTIALLY_REPAIRED"
    )


def test_no_progress_is_detected():
    outcome = (
        dispatch_reconciliation
        .classify_outcome(
            approval_linked=True,
            plan_hash_matches=True,
            approved_job_ids=[
                "alpha_engines",
            ],
            attempted_job_ids=[
                "alpha_engines",
            ],
            approved_successful=[],
            failed_job_ids=[],
            unapproved_job_ids=[],
            repaired_job_ids=[],
            unresolved_approved_job_ids=[
                "alpha_engines",
            ],
            step_delta=0,
            recommendation_delta=0,
        )
    )

    assert outcome == "NO_PROGRESS"


def test_repaired_jobs_are_absent_from_next_plan():
    repaired = (
        dispatch_reconciliation
        .determine_repaired_jobs(
            approved_job_ids=[
                "alpha_engines",
                "regime_intelligence",
            ],
            successful_job_ids=[
                "alpha_engines",
                "regime_intelligence",
            ],
            next_plan={
                "execution_steps": [
                    {
                        "job_id": (
                            "regime_intelligence"
                        ),
                    }
                ],
            },
        )
    )

    assert repaired == [
        "alpha_engines",
    ]


def test_receipt_append_is_idempotent(
    tmp_path: Path,
):
    path = tmp_path / "receipts.jsonl"

    receipt = {
        "receipt_id": "RECEIPT-1",
        "approval_id": "APPROVAL-1",
    }

    (
        dispatch_reconciliation
        .append_dispatch_receipt(
            receipt,
            receipt_path=path,
        )
    )

    (
        dispatch_reconciliation
        .append_dispatch_receipt(
            receipt,
            receipt_path=path,
        )
    )

    receipts = (
        dispatch_reconciliation
        .read_dispatch_receipts(
            path
        )
    )

    assert receipts == [receipt]


def test_valid_dispatch_with_no_attempts_is_no_progress():
    outcome = (
        dispatch_reconciliation
        .classify_outcome(
            approval_linked=True,
            plan_hash_matches=True,
            approved_job_ids=[
                "alpha_engines",
            ],
            attempted_job_ids=[],
            approved_successful=[],
            failed_job_ids=[],
            unapproved_job_ids=[],
            repaired_job_ids=[],
            unresolved_approved_job_ids=[
                "alpha_engines",
            ],
            step_delta=0,
            recommendation_delta=0,
        )
    )

    assert outcome == "NO_PROGRESS"


def test_receipt_id_is_stable_across_reconciliation_times():
    first = (
        dispatch_reconciliation
        .build_receipt_id(
            approval_id="APPROVAL-1",
            run_id="ORCH-1",
            reconciled_at=(
                "2026-07-12T12:00:00+00:00"
            ),
        )
    )

    second = (
        dispatch_reconciliation
        .build_receipt_id(
            approval_id="APPROVAL-1",
            run_id="ORCH-1",
            reconciled_at=(
                "2026-07-12T13:00:00+00:00"
            ),
        )
    )

    assert first == second
