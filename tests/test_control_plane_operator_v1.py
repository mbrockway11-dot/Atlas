"""Tests for Phase F.2 guarded operator services."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from atlas.investment import (
    control_plane_operator,
)


def plan_with_jobs(
    *job_ids: str,
) -> dict:
    return {
        "version": "1.0.0",
        "plan_status": "READY",
        "source_health_status": "DEGRADED",
        "execution": {
            "authorized": False,
            "executable": True,
            "mode": "EXECUTE",
        },
        "counts": {
            "source_recommendations": 1,
            "execution_steps": len(
                job_ids
            ),
        },
        "execution_steps": [
            {
                "step": index,
                "job_id": job_id,
                "dependencies": "",
                "command": (
                    f"python {job_id}.py"
                ),
                "output_path": (
                    f"{job_id}.json"
                ),
            }
            for index, job_id
            in enumerate(
                job_ids,
                start=1,
            )
        ],
    }


def test_preflight_prunes_current_jobs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    plan_path = tmp_path / "plan.json"

    plan = plan_with_jobs(
        "alpha_engines",
        "macro_intelligence",
    )

    plan_path.write_text(
        json.dumps(plan),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        control_plane_operator,
        "build_system_health",
        lambda: {},
    )

    monkeypatch.setattr(
        control_plane_operator,
        "build_remediation_plan",
        lambda health: plan,
    )

    monkeypatch.setattr(
        control_plane_operator,
        "load_current_schedule",
        lambda: pd.DataFrame([
            {
                "job_id": "alpha_engines",
                "status": "CURRENT",
            },
            {
                "job_id": "macro_intelligence",
                "status": "READY",
            },
        ]),
    )

    monkeypatch.setenv(
        "ATLAS_APPROVAL_SECRET",
        "secret",
    )

    result = (
        control_plane_operator
        .build_operator_preflight(
            stored_plan_path=plan_path
        )
    )

    assert result["success"]

    assert result[
        "eligible_job_ids"
    ] == [
        "macro_intelligence",
    ]

    assert result[
        "pruned_current_job_ids"
    ] == [
        "alpha_engines",
    ]


def test_stale_plan_blocks_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    plan_path = tmp_path / "plan.json"

    stored = plan_with_jobs(
        "alpha_engines"
    )

    current = plan_with_jobs(
        "macro_intelligence"
    )

    plan_path.write_text(
        json.dumps(stored),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        control_plane_operator,
        "build_system_health",
        lambda: {},
    )

    monkeypatch.setattr(
        control_plane_operator,
        "build_remediation_plan",
        lambda health: current,
    )

    monkeypatch.setattr(
        control_plane_operator,
        "load_current_schedule",
        lambda: pd.DataFrame(),
    )

    result = (
        control_plane_operator
        .build_operator_preflight(
            stored_plan_path=plan_path
        )
    )

    assert not result["success"]
    assert result[
        "status"
    ] == "STALE_PLAN"


def test_no_ready_jobs_blocks_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    plan_path = tmp_path / "plan.json"

    plan = plan_with_jobs(
        "alpha_engines"
    )

    plan_path.write_text(
        json.dumps(plan),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        control_plane_operator,
        "build_system_health",
        lambda: {},
    )

    monkeypatch.setattr(
        control_plane_operator,
        "build_remediation_plan",
        lambda health: plan,
    )

    monkeypatch.setattr(
        control_plane_operator,
        "load_current_schedule",
        lambda: pd.DataFrame([
            {
                "job_id": "alpha_engines",
                "status": "CURRENT",
            }
        ]),
    )

    monkeypatch.setenv(
        "ATLAS_APPROVAL_SECRET",
        "secret",
    )

    result = (
        control_plane_operator
        .build_operator_preflight(
            stored_plan_path=plan_path
        )
    )

    assert not result["success"]

    assert result[
        "status"
    ] == "NO_ELIGIBLE_WORK"


def test_approval_requires_exact_confirmation(
    tmp_path: Path,
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
        "build_operator_preflight",
        lambda **kwargs: {
            "success": True,
            "status": "READY",
            "approval_confirmation": (
                "APPROVE abc123"
            ),
            "effective_plan": (
                plan_with_jobs(
                    "alpha_engines"
                )
            ),
        },
    )

    with pytest.raises(
        ValueError,
        match="confirmation mismatch",
    ):
        (
            control_plane_operator
            .create_guarded_approval(
                approved_by="tester",
                confirmation="wrong",
                approved_plan_path=(
                    tmp_path
                    / "approved.json"
                ),
                approval_path=(
                    tmp_path
                    / "approval.json"
                ),
            )
        )


def test_dispatch_preflight_rejects_changed_scope(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        control_plane_operator,
        "load_optional_json",
        lambda path: (
            {
                "plan_status": "READY",
                "execution_steps": [
                    {
                        "job_id": (
                            "alpha_engines"
                        ),
                    }
                ],
            }
            if "approved" in str(path)
            else {
                "approval_id": "APPROVAL-1",
                "approved_job_ids": [
                    "alpha_engines",
                ],
            }
        ),
    )

    monkeypatch.setattr(
        control_plane_operator,
        "validate_approval",
        lambda **kwargs: {
            "valid": True,
            "errors": [],
        },
    )

    monkeypatch.setattr(
        control_plane_operator,
        "load_current_schedule",
        lambda: pd.DataFrame([
            {
                "job_id": "alpha_engines",
                "status": "CURRENT",
            }
        ]),
    )

    result = (
        control_plane_operator
        .build_dispatch_preflight(
            approved_plan_path=Path(
                "approved.json"
            ),
            approval_path=Path(
                "approval.json"
            ),
        )
    )

    assert not result["success"]

    assert result[
        "status"
    ] == "APPROVED_SCOPE_CHANGED"


def test_dispatch_requires_exact_confirmation(
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
        "evaluate_separation_of_duties",
        lambda **kwargs: {
            "allowed": True,
            "reason": (
                "SEPARATION_OF_DUTIES_SATISFIED"
            ),
        },
    )

    monkeypatch.setattr(
        control_plane_operator,
        "build_dispatch_preflight",
        lambda **kwargs: {
            "success": True,
            "status": "READY",
            "dispatch_confirmation": (
                "DISPATCH APPROVAL-1"
            ),
        },
    )

    with pytest.raises(
        ValueError,
        match="confirmation mismatch",
    ):
        (
            control_plane_operator
            .dispatch_guarded_approval(
                confirmation="wrong",
                    operator_id="tester"
            )
        )


def test_reconciliation_requires_used_approval(
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
        "load_optional_json",
        lambda path: {
            "used": False,
        },
    )

    with pytest.raises(
        ValueError,
        match="has not been dispatched",
    ):
        (
            control_plane_operator
            .reconcile_guarded_dispatch(
                    operator_id="tester",)
        )
