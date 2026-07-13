"""Tests for E.3 signed remediation approvals."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from atlas.investment import (
    control_plane_approval,
)


SECRET = "test-secret"


def ready_plan():
    return {
        "version": "1.0.0",
        "plan_status": "READY",
        "source_health_status": "DEGRADED",
        "execution": {
            "executable": True,
            "mode": "EXECUTE",
        },
        "execution_steps": [
            {
                "step": 1,
                "job_id": "alpha_engines",
                "dependencies": "",
                "command": "python alpha.py",
                "output_path": "alpha.json",
            },
            {
                "step": 2,
                "job_id": "regime_intelligence",
                "dependencies": (
                    "alpha_engines"
                ),
                "command": "python regime.py",
                "output_path": "regime.json",
            },
        ],
    }


def test_plan_hash_is_deterministic():
    plan = ready_plan()

    assert (
        control_plane_approval
        .remediation_plan_hash(plan)
        == control_plane_approval
        .remediation_plan_hash(plan)
    )


def test_valid_approval_passes():
    now = datetime(
        2026,
        7,
        12,
        tzinfo=UTC,
    )

    plan = ready_plan()

    approval = (
        control_plane_approval
        .create_approval(
            plan,
            approved_by="tester",
            ttl_minutes=30,
            secret=SECRET,
            now=now,
        )
    )

    result = (
        control_plane_approval
        .validate_approval(
            plan=plan,
            approval=approval,
            secret=SECRET,
            now=now
            + timedelta(minutes=1),
        )
    )

    assert result["valid"]
    assert result["errors"] == []


def test_modified_plan_invalidates_approval():
    plan = ready_plan()

    approval = (
        control_plane_approval
        .create_approval(
            plan,
            approved_by="tester",
            secret=SECRET,
        )
    )

    plan["execution_steps"][0][
        "command"
    ] = "python changed.py"

    result = (
        control_plane_approval
        .validate_approval(
            plan=plan,
            approval=approval,
            secret=SECRET,
        )
    )

    assert not result["valid"]
    assert (
        "PLAN_HASH_MISMATCH"
        in result["errors"]
    )


def test_expired_approval_is_rejected():
    now = datetime(
        2026,
        7,
        12,
        tzinfo=UTC,
    )

    plan = ready_plan()

    approval = (
        control_plane_approval
        .create_approval(
            plan,
            approved_by="tester",
            ttl_minutes=1,
            secret=SECRET,
            now=now,
        )
    )

    result = (
        control_plane_approval
        .validate_approval(
            plan=plan,
            approval=approval,
            secret=SECRET,
            now=now
            + timedelta(minutes=2),
        )
    )

    assert not result["valid"]
    assert (
        "APPROVAL_EXPIRED"
        in result["errors"]
    )


def test_partial_approval_authorizes_prefix():
    plan = ready_plan()

    approval = (
        control_plane_approval
        .create_approval(
            plan,
            approved_by="tester",
            max_steps=1,
            secret=SECRET,
        )
    )

    assert approval[
        "approved_job_ids"
    ] == ["alpha_engines"]

    assert approval[
        "max_steps"
    ] == 1


def test_used_approval_is_rejected():
    plan = ready_plan()

    approval = (
        control_plane_approval
        .create_approval(
            plan,
            approved_by="tester",
            secret=SECRET,
        )
    )

    approval["used"] = True

    # Re-sign the intentionally modified record.
    approval["signature"] = (
        control_plane_approval
        .sign_approval(
            approval,
            secret=SECRET,
        )
    )

    result = (
        control_plane_approval
        .validate_approval(
            plan=plan,
            approval=approval,
            secret=SECRET,
        )
    )

    assert not result["valid"]
    assert (
        "APPROVAL_ALREADY_USED"
        in result["errors"]
    )
