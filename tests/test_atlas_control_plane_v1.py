"""Tests for Phase E.1 Atlas Control Plane."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from atlas.investment import (
    control_plane,
)


def healthy_component():
    return {
        "status": "HEALTHY",
        "summary": "Healthy.",
        "metrics": {},
        "issues": [],
    }


def test_overall_status_uses_worst_component():
    assert control_plane.derive_overall_status({
        "a": healthy_component(),
        "b": {
            "status": "DEGRADED",
            "summary": "",
            "metrics": {},
            "issues": [],
        },
    }) == "DEGRADED"

    assert control_plane.derive_overall_status({
        "a": healthy_component(),
        "b": {
            "status": "CRITICAL",
            "summary": "",
            "metrics": {},
            "issues": [],
        },
    }) == "CRITICAL"


def test_scheduler_health_is_degraded_when_ready():
    report = {
        "counts": {
            "total_jobs": 2,
            "current_jobs": 1,
            "ready_jobs": 1,
            "blocked_jobs": 0,
            "failed_jobs": 0,
            "dirty_jobs": 1,
        }
    }

    schedule = pd.DataFrame([
        {
            "job_id": "a",
            "status": "CURRENT",
        },
        {
            "job_id": "b",
            "status": "READY",
        },
    ])

    result = (
        control_plane.build_scheduler_health(
            scheduler_report=report,
            schedule=schedule,
        )
    )

    assert result["status"] == "DEGRADED"
    assert result["metrics"][
        "ready_jobs"
    ] == 1
    assert "READY:b" in result["issues"]


def test_provenance_count_mismatch_is_critical():
    result = (
        control_plane.build_provenance_health(
            events=[
                {
                    "event_id": "PROV-1",
                    "run_id": "RUN-1",
                    "job_id": "a",
                    "status": "SUCCEEDED",
                    "build_identity_hash": "x",
                    "required_input_manifest": {},
                    "required_output_manifest": {},
                }
            ],
            latest={
                "event_count": 0,
                "jobs": {},
            },
        )
    )

    assert result["status"] == "CRITICAL"
    assert (
        "LATEST_INDEX_COUNT_MISMATCH"
        in result["issues"]
    )


def test_resume_checkpoint_creates_action():
    components = {
        "architecture": healthy_component(),
        "artifact_contracts": (
            healthy_component()
        ),
        "artifact_lineage": (
            healthy_component()
        ),
        "scheduler": healthy_component(),
        "build_cache": {
            "status": "HEALTHY",
            "summary": "",
            "metrics": {
                "cache_entries": 1,
            },
            "issues": [],
        },
        "execution": healthy_component(),
        "provenance": healthy_component(),
    }

    actions = (
        control_plane.build_recommended_actions(
            components=components,
            schedule=pd.DataFrame(),
            contract_audit={
                "failed_job_contracts": [],
            },
            lineage_audit={
                "incomplete_job_inputs": [],
            },
            execution_state={
                "resumable": True,
                "run_id": "ORCH-1",
            },
        )
    )

    matches = [
        item
        for item in actions
        if item["action_type"]
        == "RESUME_INTERRUPTED_CYCLE"
    ]

    assert len(matches) == 1
    assert (
        "--resume"
        in matches[0][
            "recommended_command"
        ]
    )


def test_actions_are_ordered_by_severity():
    components = {
        "architecture": {
            "status": "CRITICAL",
            "summary": "",
            "metrics": {},
            "issues": ["broken"],
        },
        "artifact_contracts": (
            healthy_component()
        ),
        "artifact_lineage": (
            healthy_component()
        ),
        "scheduler": healthy_component(),
        "build_cache": {
            "status": "HEALTHY",
            "summary": "",
            "metrics": {
                "cache_entries": 0,
            },
            "issues": [],
        },
        "execution": healthy_component(),
        "provenance": healthy_component(),
    }

    actions = (
        control_plane.build_recommended_actions(
            components=components,
            schedule=pd.DataFrame(),
            contract_audit={
                "failed_job_contracts": [],
            },
            lineage_audit={
                "incomplete_job_inputs": [],
            },
            execution_state={},
        )
    )

    assert actions[0]["severity"] == (
        "CRITICAL"
    )
    assert actions[-1]["severity"] == (
        "INFO"
    )


def test_control_plane_outputs_are_written(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    health_json = (
        tmp_path / "health.json"
    )
    health_csv = (
        tmp_path / "health.csv"
    )
    actions_csv = (
        tmp_path / "actions.csv"
    )
    health_md = (
        tmp_path / "health.md"
    )

    monkeypatch.setattr(
        control_plane,
        "OUTPUT_DIR",
        tmp_path,
    )
    monkeypatch.setattr(
        control_plane,
        "SYSTEM_HEALTH_JSON",
        health_json,
    )
    monkeypatch.setattr(
        control_plane,
        "SYSTEM_HEALTH_CSV",
        health_csv,
    )
    monkeypatch.setattr(
        control_plane,
        "RECOMMENDED_ACTIONS_CSV",
        actions_csv,
    )
    monkeypatch.setattr(
        control_plane,
        "SYSTEM_HEALTH_MD",
        health_md,
    )

    report = {
        "overall_status": "HEALTHY",
        "generated_at": (
            "2026-07-12T00:00:00+00:00"
        ),
        "counts": {
            "recommended_actions": 1,
        },
        "component_rows": [
            {
                "component": "scheduler",
                "status": "HEALTHY",
                "summary": "Healthy.",
                "issue_count": 0,
                "metrics_json": "{}",
            }
        ],
        "recommended_actions": [
            {
                "action_rank": 1,
                "severity": "INFO",
                "category": "system",
                "target": "atlas",
                "action_type": (
                    "NO_ACTION_REQUIRED"
                ),
                "reason": "Healthy.",
                "recommended_command": "",
            }
        ],
    }

    control_plane.write_system_health_outputs(
        report
    )

    assert health_json.exists()
    assert health_csv.exists()
    assert actions_csv.exists()
    assert health_md.exists()

    payload = json.loads(
        health_json.read_text(
            encoding="utf-8"
        )
    )

    assert payload[
        "overall_status"
    ] == "HEALTHY"


def test_component_rows_are_flat():
    rows = (
        control_plane.build_component_rows({
            "scheduler": {
                "status": "HEALTHY",
                "summary": "Current.",
                "metrics": {
                    "current_jobs": 30,
                },
                "issues": [],
            }
        })
    )

    assert rows[0][
        "component"
    ] == "scheduler"
    assert rows[0][
        "issue_count"
    ] == 0
    assert json.loads(
        rows[0]["metrics_json"]
    )[
        "current_jobs"
    ] == 30
