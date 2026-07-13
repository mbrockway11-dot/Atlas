"""Tests for E.3 controlled Atlas dispatch."""

from __future__ import annotations

import pytest

from atlas.investment import (
    control_plane_dispatch,
)


def test_dispatch_restricts_cycle_to_approved_jobs(
    monkeypatch: pytest.MonkeyPatch,
):
    plan = {
        "execution": {
            "mode": "EXECUTE",
        }
    }

    approval = {
        "approval_id": "APPROVAL-1",
    }

    monkeypatch.setattr(
        control_plane_dispatch,
        "load_json",
        lambda path: (
            plan
            if "plan" in str(path)
            else approval
        ),
    )

    monkeypatch.setattr(
        control_plane_dispatch,
        "validate_approval",
        lambda **kwargs: {
            "valid": True,
            "errors": [],
            "approval_id": "APPROVAL-1",
            "approved_by": "tester",
            "approved_job_ids": [
                "alpha_engines",
                "regime_intelligence",
            ],
        },
    )

    captured = {}

    def fake_cycle(**kwargs):
        captured.update(kwargs)

        return {
            "run_id": "ORCH-1",
            "failure_detected": False,
        }

    monkeypatch.setattr(
        control_plane_dispatch,
        "run_research_cycle",
        fake_cycle,
    )

    monkeypatch.setattr(
        control_plane_dispatch,
        "mark_approval_used",
        lambda *args, **kwargs: {},
    )

    result = (
        control_plane_dispatch
        .dispatch_approved_plan()
    )

    assert result["success"]

    assert captured[
        "allowed_job_ids"
    ] == {
        "alpha_engines",
        "regime_intelligence",
    }

    assert captured[
        "max_jobs"
    ] == 2

    assert captured[
        "execute"
    ] is True


def test_invalid_approval_never_dispatches(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        control_plane_dispatch,
        "load_json",
        lambda path: {},
    )

    monkeypatch.setattr(
        control_plane_dispatch,
        "validate_approval",
        lambda **kwargs: {
            "valid": False,
            "errors": [
                "SIGNATURE_INVALID"
            ],
        },
    )

    called = False

    def fake_cycle(**kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(
        control_plane_dispatch,
        "run_research_cycle",
        fake_cycle,
    )

    with pytest.raises(
        ValueError,
        match="SIGNATURE_INVALID",
    ):
        (
            control_plane_dispatch
            .dispatch_approved_plan()
        )

    assert not called
