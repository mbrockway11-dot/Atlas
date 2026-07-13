"""Tests for Phase F.1 Control Plane dashboard view model."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from atlas.investment import (
    control_plane_dashboard,
)


def test_approval_summary_hides_sensitive_fields():
    summary = (
        control_plane_dashboard
        .safe_approval_summary({
            "approval_id": "APPROVAL-1",
            "approved_by": "tester",
            "approved_job_ids": [
                "alpha_engines",
            ],
            "signature": "secret-signature",
            "nonce": "secret-nonce",
            "used": False,
        })
    )

    assert summary["present"]
    assert (
        summary["approval_id"]
        == "APPROVAL-1"
    )
    assert "signature" not in summary
    assert "nonce" not in summary


def test_empty_approval_is_normalized():
    summary = (
        control_plane_dashboard
        .safe_approval_summary({})
    )

    assert not summary["present"]
    assert (
        summary["approved_job_ids"]
        == []
    )


def test_reconciliation_summary_is_safe():
    summary = (
        control_plane_dashboard
        .safe_reconciliation_summary({
            "outcome": "NO_PROGRESS",
            "summary": "No work.",
            "receipt": {
                "scope_valid": True,
                "plan_hash_matches": True,
                "approved_job_ids": [
                    "alpha_engines",
                ],
                "attempted_job_ids": [],
                "repaired_job_ids": [],
                "unapproved_job_ids": [],
            },
        })
    )

    assert summary["present"]
    assert (
        summary["outcome"]
        == "NO_PROGRESS"
    )
    assert summary["scope_valid"]


def test_provenance_event_is_flattened():
    event = (
        control_plane_dashboard
        .sanitize_provenance_event({
            "event_id": "PROV-1",
            "run_id": "ORCH-1",
            "job_id": "alpha_engines",
            "status": "SUCCEEDED",
            "attempt": 1,
            "duration_seconds": 2.5,
            "cache": {
                "hit": True,
            },
            "verification": {
                "verified": True,
                "healed": True,
            },
            "required_input_manifest": {
                "secret-path": "hash",
            },
        })
    )

    assert event["cache_hit"]
    assert event[
        "artifact_verified"
    ]
    assert (
        "required_input_manifest"
        not in event
    )


def test_json_loader_handles_missing_file(
    tmp_path: Path,
):
    assert (
        control_plane_dashboard
        .load_json_object(
            tmp_path / "missing.json"
        )
        == {}
    )


def test_dataframe_records_replace_nan():
    frame = pd.DataFrame([
        {
            "job_id": "a",
            "reason": float("nan"),
        }
    ])

    rows = (
        control_plane_dashboard
        .dataframe_records(frame)
    )

    assert rows[0]["reason"] is None


def test_dashboard_model_uses_canonical_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    schedule_path = (
        tmp_path / "schedule.csv"
    )

    pd.DataFrame([
        {
            "job_id": "alpha_engines",
            "status": "CURRENT",
        }
    ]).to_csv(
        schedule_path,
        index=False,
    )

    monkeypatch.setattr(
        control_plane_dashboard,
        "build_and_write_system_health",
        lambda: {
            "overall_status": "HEALTHY",
            "summary": "Healthy.",
            "generated_at": "now",
            "counts": {
                "healthy_components": 7,
            },
            "components": {
                "scheduler": {
                    "status": "HEALTHY",
                    "summary": "Current.",
                    "metrics": {
                        "current_jobs": 1,
                    },
                    "issues": [],
                }
            },
            "recommended_actions": [],
        },
    )

    monkeypatch.setattr(
        control_plane_dashboard,
        "build_and_write_remediation_plan",
        lambda health: {
            "plan_status": "NO_ACTION",
            "summary": "No action.",
            "counts": {},
            "execution": {
                "authorized": False,
                "executable": False,
                "mode": "NONE",
            },
            "execution_steps": [],
            "manual_actions": [],
            "informational_actions": [],
        },
    )

    monkeypatch.setattr(
        control_plane_dashboard,
        "build_research_scheduler_report",
        lambda: {
            "counts": {
                "current_jobs": 1,
            },
            "outputs": {
                "research_schedule_csv": str(
                    schedule_path
                ),
            },
        },
    )

    monkeypatch.setattr(
        control_plane_dashboard,
        "load_json_object",
        lambda path: {},
    )

    monkeypatch.setattr(
        control_plane_dashboard,
        "read_provenance_events",
        lambda: [],
    )

    monkeypatch.setattr(
        control_plane_dashboard,
        "load_latest_provenance",
        lambda: {},
    )

    monkeypatch.setattr(
        control_plane_dashboard,
        "read_dispatch_receipts",
        lambda: [],
    )

    model = (
        control_plane_dashboard
        .build_control_plane_dashboard_model()
    )

    assert model[
        "overall_status"
    ] == "HEALTHY"

    assert model["read_only"]

    assert model[
        "scheduler"
    ][
        "rows"
    ][0][
        "job_id"
    ] == "alpha_engines"

    assert not model[
        "contract"
    ][
        "approval_actions_exposed"
    ]
