"""Tests for Phase E.2 deterministic remediation planning."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.investment import (
    control_plane_remediation,
)


def health_report(
    actions,
    *,
    status="DEGRADED",
):
    return {
        "overall_status": status,
        "recommended_actions": actions,
        "components": {
            "execution": {
                "metrics": {},
            }
        },
    }


def test_job_repair_set_includes_upstream_dependencies():
    repair_set = (
        control_plane_remediation
        .expand_job_repair_set(
            "research_experiment_execution"
        )
    )

    assert (
        "research_experiment_execution"
        in repair_set
    )
    assert (
        "research_experiment_designer"
        in repair_set
    )
    assert (
        "research_program_manager"
        in repair_set
    )


def test_duplicate_recommendations_produce_one_job_step():
    plan = (
        control_plane_remediation
        .build_remediation_plan(
            health_report([
                {
                    "severity": "HIGH",
                    "category": (
                        "artifact_contract"
                    ),
                    "action_type": (
                        "REBUILD_REQUIRED_OUTPUTS"
                    ),
                    "target": (
                        "historical_alpha_validation"
                    ),
                },
                {
                    "severity": "HIGH",
                    "category": (
                        "artifact_lineage"
                    ),
                    "action_type": (
                        "RESTORE_REQUIRED_INPUTS"
                    ),
                    "target": (
                        "historical_alpha_validation"
                    ),
                },
            ])
        )
    )

    job_ids = [
        item["job_id"]
        for item in plan[
            "execution_steps"
        ]
    ]

    assert len(job_ids) == len(
        set(job_ids)
    )
    assert (
        "historical_alpha_validation"
        in job_ids
    )


def test_execution_steps_follow_canonical_order():
    plan = (
        control_plane_remediation
        .build_remediation_plan(
            health_report([
                {
                    "severity": "HIGH",
                    "action_type": (
                        "REBUILD_REQUIRED_OUTPUTS"
                    ),
                    "target": (
                        "research_experiment_execution"
                    ),
                }
            ])
        )
    )

    jobs = [
        step["job_id"]
        for step in plan[
            "execution_steps"
        ]
    ]

    designer_index = jobs.index(
        "research_experiment_designer"
    )

    execution_index = jobs.index(
        "research_experiment_execution"
    )

    assert (
        designer_index
        < execution_index
    )


def test_structural_error_blocks_execution():
    plan = (
        control_plane_remediation
        .build_remediation_plan(
            health_report(
                [
                    {
                        "severity": "CRITICAL",
                        "action_type": (
                            "REPAIR_STRUCTURAL_CONTRACT"
                        ),
                        "target": "broken",
                        "reason": "Broken.",
                    },
                    {
                        "severity": "HIGH",
                        "action_type": (
                            "EXECUTE_READY_JOB"
                        ),
                        "target": (
                            "alpha_engines"
                        ),
                    },
                ],
                status="CRITICAL",
            )
        )
    )

    assert plan[
        "plan_status"
    ] == "BLOCKED"

    assert not plan[
        "execution"
    ][
        "executable"
    ]

    assert plan[
        "execution_steps"
    ][0][
        "blocked_by_structure"
    ]


def test_resumable_cycle_selects_resume_mode():
    report = health_report([
        {
            "severity": "HIGH",
            "action_type": (
                "RESUME_INTERRUPTED_CYCLE"
            ),
            "target": "ORCH-1",
        },
        {
            "severity": "MEDIUM",
            "action_type": (
                "EXECUTE_READY_JOB"
            ),
            "target": "alpha_engines",
        },
    ])

    report["components"][
        "execution"
    ][
        "metrics"
    ][
        "run_id"
    ] = "ORCH-1"

    plan = (
        control_plane_remediation
        .build_remediation_plan(
            report
        )
    )

    assert plan[
        "execution"
    ][
        "mode"
    ] == "RESUME"

    assert (
        "--resume"
        in plan[
            "execution"
        ][
            "recommended_command"
        ]
    )


def test_no_actions_produce_no_action_plan():
    plan = (
        control_plane_remediation
        .build_remediation_plan(
            health_report([
                {
                    "severity": "INFO",
                    "action_type": (
                        "NO_ACTION_REQUIRED"
                    ),
                    "target": "atlas",
                }
            ], status="HEALTHY")
        )
    )

    assert plan[
        "plan_status"
    ] == "NO_ACTION"

    assert plan[
        "execution_steps"
    ] == []


def test_unknown_job_target_requires_manual_review():
    plan = (
        control_plane_remediation
        .build_remediation_plan(
            health_report([
                {
                    "severity": "HIGH",
                    "action_type": (
                        "REBUILD_REQUIRED_OUTPUTS"
                    ),
                    "target": "not_a_job",
                }
            ])
        )
    )

    assert plan[
        "plan_status"
    ] == "MANUAL_REVIEW"

    assert plan[
        "manual_actions"
    ][0][
        "action_type"
    ] == "RESOLVE_UNKNOWN_JOB_TARGET"


def test_outputs_are_written(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    json_path = (
        tmp_path / "plan.json"
    )
    csv_path = (
        tmp_path / "plan.csv"
    )
    md_path = (
        tmp_path / "plan.md"
    )

    monkeypatch.setattr(
        control_plane_remediation,
        "OUTPUT_DIR",
        tmp_path,
    )
    monkeypatch.setattr(
        control_plane_remediation,
        "REMEDIATION_PLAN_JSON",
        json_path,
    )
    monkeypatch.setattr(
        control_plane_remediation,
        "REMEDIATION_PLAN_CSV",
        csv_path,
    )
    monkeypatch.setattr(
        control_plane_remediation,
        "REMEDIATION_PLAN_MD",
        md_path,
    )

    plan = {
        "plan_status": "NO_ACTION",
        "source_health_status": "HEALTHY",
        "execution": {
            "mode": "NONE",
            "authorized": False,
            "recommended_command": "",
        },
        "execution_steps": [],
        "manual_actions": [],
        "informational_actions": [],
    }

    control_plane_remediation.write_remediation_outputs(
        plan
    )

    assert json_path.exists()
    assert csv_path.exists()
    assert md_path.exists()

    loaded = json.loads(
        json_path.read_text(
            encoding="utf-8"
        )
    )

    assert loaded[
        "plan_status"
    ] == "NO_ACTION"
