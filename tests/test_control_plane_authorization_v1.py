"""Tests for Phase F.4 operator role authorization."""

from __future__ import annotations

import pytest

from atlas.investment import (
    control_plane_authorization,
)


def test_unknown_identity_defaults_to_viewer():
    role = (
        control_plane_authorization
        .resolve_operator_role(
            "unknown",
            assignments={},
        )
    )

    assert role == "VIEWER"


def test_role_assignments_are_case_insensitive():
    role = (
        control_plane_authorization
        .resolve_operator_role(
            "MICHAEL BROCKWAY",
            assignments={
                "michael brockway": (
                    "ADMINISTRATOR"
                ),
            },
        )
    )

    assert role == "ADMINISTRATOR"


def test_viewer_cannot_create_approval():
    decision = (
        control_plane_authorization
        .authorize_operator(
            operator_id="viewer",
            permission=(
                "CREATE_APPROVAL"
            ),
            assignments={
                "viewer": "VIEWER",
            },
        )
    )

    assert not decision.allowed


def test_approver_can_approve_but_not_dispatch():
    approve = (
        control_plane_authorization
        .authorize_operator(
            operator_id="alice",
            permission=(
                "CREATE_APPROVAL"
            ),
            assignments={
                "alice": "APPROVER",
            },
        )
    )

    dispatch = (
        control_plane_authorization
        .authorize_operator(
            operator_id="alice",
            permission=(
                "DISPATCH_APPROVAL"
            ),
            assignments={
                "alice": "APPROVER",
            },
        )
    )

    assert approve.allowed
    assert not dispatch.allowed


def test_dispatcher_can_dispatch_but_not_approve():
    dispatch = (
        control_plane_authorization
        .authorize_operator(
            operator_id="bob",
            permission=(
                "DISPATCH_APPROVAL"
            ),
            assignments={
                "bob": "DISPATCHER",
            },
        )
    )

    approve = (
        control_plane_authorization
        .authorize_operator(
            operator_id="bob",
            permission=(
                "CREATE_APPROVAL"
            ),
            assignments={
                "bob": "DISPATCHER",
            },
        )
    )

    assert dispatch.allowed
    assert not approve.allowed


def test_administrator_has_all_permissions():
    capabilities = (
        control_plane_authorization
        .build_operator_capabilities(
            "admin"
        )
    )

    # Environment-independent assertion through role table.
    permissions = (
        control_plane_authorization
        .permissions_for_role(
            "ADMINISTRATOR"
        )
    )

    assert permissions == (
        control_plane_authorization
        .PERMISSIONS
    )


def test_high_risk_requires_different_operators():
    decision = (
        control_plane_authorization
        .evaluate_separation_of_duties(
            approved_by="Michael",
            dispatched_by="Michael",
            approved_job_count=4,
            high_risk_threshold=3,
        )
    )

    assert not decision["allowed"]
    assert decision["high_risk"]


def test_low_risk_allows_same_operator():
    decision = (
        control_plane_authorization
        .evaluate_separation_of_duties(
            approved_by="Michael",
            dispatched_by="Michael",
            approved_job_count=1,
            high_risk_threshold=3,
        )
    )

    assert decision["allowed"]
    assert not decision["high_risk"]


def test_require_permission_raises():
    with pytest.raises(
        PermissionError,
        match="authorization denied",
    ):
        (
            control_plane_authorization
            .require_permission(
                operator_id="viewer",
                permission=(
                    "CREATE_APPROVAL"
                ),
            )
        )
