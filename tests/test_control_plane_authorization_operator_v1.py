"""Integration tests for F.4 operator permission enforcement."""

from __future__ import annotations

import pytest

from atlas.investment import (
    control_plane_operator,
)


def test_approval_checks_permission_first(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        control_plane_operator,
        "require_permission",
        lambda **kwargs: (
            (_ for _ in ()).throw(
                PermissionError(
                    "denied"
                )
            )
        ),
    )

    called = False

    def fake_preflight(**kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(
        control_plane_operator,
        "build_operator_preflight",
        fake_preflight,
    )

    with pytest.raises(
        PermissionError,
        match="denied",
    ):
        (
            control_plane_operator
            .create_guarded_approval(
                approved_by="viewer",
                operator_id="viewer",
                session_id="UI-1",
                confirmation="",
            )
        )

    assert not called


def test_dispatch_separation_policy_blocks_high_risk(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        control_plane_operator,
        "require_permission",
        lambda **kwargs: {
            "allowed": True,
            "role": "ADMINISTRATOR",
        },
    )

    monkeypatch.setattr(
        control_plane_operator,
        "build_dispatch_preflight",
        lambda **kwargs: {
            "success": True,
            "status": "READY",
            "reason": "ready",
            "approval_id": "APPROVAL-1",
            "approved_by": "Michael",
            "approved_job_ids": [
                "a",
                "b",
                "c",
                "d",
            ],
            "dispatch_confirmation": (
                "DISPATCH APPROVAL-1"
            ),
        },
    )

    monkeypatch.setattr(
        control_plane_operator,
        "evaluate_separation_of_duties",
        lambda **kwargs: {
            "allowed": False,
            "reason": (
                "HIGH_RISK_APPROVER_"
                "DISPATCHER_MUST_DIFFER"
            ),
        },
    )

    monkeypatch.setattr(
        control_plane_operator,
        "audit_operator_action",
        lambda **kwargs: kwargs,
    )

    with pytest.raises(
        PermissionError,
        match="separation-of-duties",
    ):
        (
            control_plane_operator
            .dispatch_guarded_approval(
                confirmation=(
                    "DISPATCH APPROVAL-1"
                ),
                operator_id="Michael",
                session_id="UI-1",
            )
        )


def test_reconciliation_requires_permission(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        control_plane_operator,
        "require_permission",
        lambda **kwargs: (
            (_ for _ in ()).throw(
                PermissionError(
                    "denied"
                )
            )
        ),
    )

    with pytest.raises(
        PermissionError,
        match="denied",
    ):
        (
            control_plane_operator
            .reconcile_guarded_dispatch(
                operator_id="viewer",
                session_id="UI-1",
            )
        )
