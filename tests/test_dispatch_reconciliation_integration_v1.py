"""Integration-style tests for E.4 reconciliation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.investment import (
    dispatch_reconciliation,
)


def test_reconciliation_detects_repaired_approved_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    approval_path = (
        tmp_path / "approval.json"
    )
    plan_path = (
        tmp_path / "plan.json"
    )
    receipts_path = (
        tmp_path / "receipts.jsonl"
    )

    approval = {
        "approval_id": "APPROVAL-1",
        "approved_by": "tester",
        "approved_job_ids": [
            "alpha_engines",
        ],
        "used": True,
        "used_at": (
            "2026-07-12T12:00:00+00:00"
        ),
        "dispatch_run_id": "ORCH-1",
    }

    plan = {
        "version": "1.0.0",
        "plan_status": "READY",
        "source_health_status": (
            "DEGRADED"
        ),
        "execution": {
            "mode": "EXECUTE",
        },
        "execution_steps": [
            {
                "step": 1,
                "job_id": "alpha_engines",
                "dependencies": "",
                "command": "python alpha.py",
                "output_path": "alpha.json",
            }
        ],
        "counts": {
            "source_recommendations": 1,
            "execution_steps": 1,
        },
    }

    plan_hash = (
        dispatch_reconciliation
        .remediation_plan_hash(
            plan
        )
    )

    approval["plan_hash"] = (
        plan_hash
    )

    approval_path.write_text(
        json.dumps(approval),
        encoding="utf-8",
    )

    plan_path.write_text(
        json.dumps(plan),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        dispatch_reconciliation,
        "read_provenance_events",
        lambda: [
            {
                "run_id": "ORCH-1",
                "job_id": "alpha_engines",
                "status": "SUCCEEDED",
            }
        ],
    )

    monkeypatch.setattr(
        dispatch_reconciliation,
        "build_and_write_system_health",
        lambda: {
            "overall_status": "HEALTHY",
            "counts": {
                "recommended_actions": 0,
            },
        },
    )

    monkeypatch.setattr(
        dispatch_reconciliation,
        "build_and_write_remediation_plan",
        lambda health: {
            "plan_status": "NO_ACTION",
            "execution": {
                "mode": "NONE",
            },
            "counts": {
                "source_recommendations": 0,
                "execution_steps": 0,
            },
            "execution_steps": [],
        },
    )

    monkeypatch.setattr(
        dispatch_reconciliation,
        "write_reconciliation_outputs",
        lambda report: None,
    )

    result = (
        dispatch_reconciliation
        .reconcile_dispatch(
            approval_path=approval_path,
            original_plan_path=plan_path,
            receipt_path=receipts_path,
        )
    )

    assert result["success"]
    assert result[
        "outcome"
    ] == "RECONCILED"

    receipt = result["receipt"]

    assert receipt[
        "scope_valid"
    ]

    assert receipt[
        "repaired_job_ids"
    ] == [
        "alpha_engines",
    ]

    assert receipt[
        "delta"
    ][
        "execution_steps_reduced"
    ] == 1


def test_unapproved_provenance_event_is_scope_violation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    approval_path = (
        tmp_path / "approval.json"
    )
    plan_path = (
        tmp_path / "plan.json"
    )
    receipts_path = (
        tmp_path / "receipts.jsonl"
    )

    plan = {
        "version": "1.0.0",
        "plan_status": "READY",
        "source_health_status": (
            "DEGRADED"
        ),
        "execution": {
            "mode": "EXECUTE",
        },
        "execution_steps": [
            {
                "step": 1,
                "job_id": "alpha_engines",
                "dependencies": "",
                "command": "python alpha.py",
                "output_path": "alpha.json",
            }
        ],
        "counts": {
            "source_recommendations": 1,
            "execution_steps": 1,
        },
    }

    approval = {
        "approval_id": "APPROVAL-1",
        "approved_by": "tester",
        "approved_job_ids": [
            "alpha_engines",
        ],
        "used": True,
        "used_at": "",
        "dispatch_run_id": "ORCH-1",
        "plan_hash": (
            dispatch_reconciliation
            .remediation_plan_hash(
                plan
            )
        ),
    }

    approval_path.write_text(
        json.dumps(approval),
        encoding="utf-8",
    )

    plan_path.write_text(
        json.dumps(plan),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        dispatch_reconciliation,
        "read_provenance_events",
        lambda: [
            {
                "run_id": "ORCH-1",
                "job_id": "alpha_engines",
                "status": "SUCCEEDED",
            },
            {
                "run_id": "ORCH-1",
                "job_id": "macro_intelligence",
                "status": "SUCCEEDED",
            },
        ],
    )

    monkeypatch.setattr(
        dispatch_reconciliation,
        "build_and_write_system_health",
        lambda: {
            "overall_status": "DEGRADED",
            "counts": {},
        },
    )

    monkeypatch.setattr(
        dispatch_reconciliation,
        "build_and_write_remediation_plan",
        lambda health: {
            "plan_status": "READY",
            "execution": {},
            "counts": {
                "source_recommendations": 1,
                "execution_steps": 1,
            },
            "execution_steps": [
                {
                    "job_id": (
                        "alpha_engines"
                    ),
                }
            ],
        },
    )

    monkeypatch.setattr(
        dispatch_reconciliation,
        "write_reconciliation_outputs",
        lambda report: None,
    )

    result = (
        dispatch_reconciliation
        .reconcile_dispatch(
            approval_path=approval_path,
            original_plan_path=plan_path,
            receipt_path=receipts_path,
        )
    )

    assert not result["success"]

    assert result[
        "outcome"
    ] == "SCOPE_VIOLATION"

    assert result[
        "receipt"
    ][
        "unapproved_job_ids"
    ] == [
        "macro_intelligence",
    ]
