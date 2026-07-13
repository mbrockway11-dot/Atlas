"""Integration-style control-plane aggregation tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from atlas.investment import (
    control_plane,
)


def test_build_system_health_from_canonical_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    schedule_path = (
        tmp_path / "schedule.csv"
    )

    pd.DataFrame([
        {
            "job_id": "alpha",
            "status": "CURRENT",
        }
    ]).to_csv(
        schedule_path,
        index=False,
    )

    monkeypatch.setattr(
        control_plane,
        "build_research_scheduler_report",
        lambda: {
            "counts": {
                "total_jobs": 1,
                "current_jobs": 1,
                "ready_jobs": 0,
                "blocked_jobs": 0,
                "failed_jobs": 0,
                "dirty_jobs": 0,
            },
            "outputs": {
                "research_schedule_csv": str(
                    schedule_path
                ),
            },
        },
    )

    monkeypatch.setattr(
        control_plane,
        "build_contract_audit",
        lambda: {
            "success": True,
            "filesystem_complete": True,
            "contract_count": 1,
            "registered_job_count": 1,
            "registered_artifact_count": 1,
            "assigned_artifact_count": 1,
            "unassigned_artifact_count": 0,
            "registry_errors": [],
            "failed_job_contracts": [],
        },
    )

    monkeypatch.setattr(
        control_plane,
        "build_lineage_audit",
        lambda: {
            "success": True,
            "filesystem_complete": True,
            "input_contract_count": 1,
            "registered_job_count": 1,
            "lineage_edge_count": 0,
            "explicit_input_artifact_count": 0,
            "registry_errors": [],
            "incomplete_job_inputs": [],
        },
    )

    monkeypatch.setattr(
        control_plane,
        "load_build_cache",
        lambda: {
            "schema_version": "1.0.0",
            "hash_algorithm": "sha256",
            "entries": {
                "alpha": {},
            },
        },
    )

    monkeypatch.setattr(
        control_plane,
        "read_provenance_events",
        lambda: [],
    )

    monkeypatch.setattr(
        control_plane,
        "load_latest_provenance",
        lambda: {
            "event_count": 0,
            "jobs": {},
        },
    )

    monkeypatch.setattr(
        control_plane,
        "load_resume_state",
        lambda: {},
    )

    report = (
        control_plane.build_system_health()
    )

    assert report[
        "overall_status"
    ] == "HEALTHY"
    assert report["success"]
    assert report["counts"][
        "healthy_components"
    ] == 7
    assert report[
        "recommended_actions"
    ][0][
        "action_type"
    ] == "NO_ACTION_REQUIRED"
