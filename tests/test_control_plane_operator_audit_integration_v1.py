"""Integration tests for operator-service audit events."""

from __future__ import annotations

import pytest

from atlas.investment import (
    control_plane_operator,
)


def test_rejected_approval_is_audited(
    monkeypatch: pytest.MonkeyPatch,
):
    events = []

    monkeypatch.setattr(
        control_plane_operator,
        "build_operator_preflight",
        lambda **kwargs: {
            "success": False,
            "status": "NO_ELIGIBLE_WORK",
            "reason": "No ready work.",
            "effective_plan_hash": "abc",
            "eligible_job_ids": [],
            "counts": {
                "eligible_steps": 0,
            },
        },
    )

    monkeypatch.setattr(
        control_plane_operator,
        "audit_operator_action",
        lambda **kwargs: events.append(
            kwargs
        ) or kwargs,
    )

    with pytest.raises(
        ValueError,
        match="Approval preflight failed",
    ):
        (
            control_plane_operator
            .create_guarded_approval(
                approved_by="tester",
                operator_id="tester",
                session_id="UI-1",
                confirmation="",
            )
        )

    assert [
        item["action"]
        for item in events
    ] == [
        "APPROVAL_ATTEMPTED",
        "APPROVAL_REJECTED",
    ]


def test_rejected_dispatch_is_audited(
    monkeypatch: pytest.MonkeyPatch,
):
    events = []

    monkeypatch.setattr(
        control_plane_operator,
        "build_dispatch_preflight",
        lambda **kwargs: {
            "success": False,
            "status": "APPROVAL_INVALID",
            "reason": "expired",
            "approval_id": "APPROVAL-1",
            "approved_by": "tester",
            "approved_job_ids": [
                "alpha_engines",
            ],
            "expires_at": "",
        },
    )

    monkeypatch.setattr(
        control_plane_operator,
        "audit_operator_action",
        lambda **kwargs: events.append(
            kwargs
        ) or kwargs,
    )

    with pytest.raises(
        ValueError,
        match="Dispatch preflight failed",
    ):
        (
            control_plane_operator
            .dispatch_guarded_approval(
                confirmation="",
                operator_id="tester",
                session_id="UI-1",
            )
        )

    assert [
        item["action"]
        for item in events
    ] == [
        "DISPATCH_ATTEMPTED",
        "DISPATCH_REJECTED",
    ]


def test_completed_reconciliation_is_audited(
    monkeypatch: pytest.MonkeyPatch,
):
    events = []

    monkeypatch.setattr(
        control_plane_operator,
        "load_optional_json",
        lambda path: {
            "used": True,
            "approval_id": "APPROVAL-1",
            "approved_by": "tester",
            "dispatch_run_id": "ORCH-1",
            "approved_job_ids": [
                "alpha_engines",
            ],
        },
    )

    monkeypatch.setattr(
        control_plane_operator,
        "reconcile_dispatch",
        lambda **kwargs: {
            "success": True,
            "outcome": "NO_PROGRESS",
            "receipt": {
                "scope_valid": True,
            },
        },
    )

    monkeypatch.setattr(
        control_plane_operator,
        "audit_operator_action",
        lambda **kwargs: events.append(
            kwargs
        ) or kwargs,
    )

    result = (
        control_plane_operator
        .reconcile_guarded_dispatch(
            operator_id="tester",
            session_id="UI-1",
        )
    )

    assert result[
        "outcome"
    ] == "NO_PROGRESS"

    assert [
        item["action"]
        for item in events
    ] == [
        "RECONCILIATION_ATTEMPTED",
        "RECONCILIATION_COMPLETED",
    ]
