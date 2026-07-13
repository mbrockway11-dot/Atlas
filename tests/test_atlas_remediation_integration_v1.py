"""Integration test for Atlas E.1 to E.2 planning."""

from __future__ import annotations

from atlas.investment.control_plane_remediation import (
    build_remediation_plan,
)


def test_degraded_health_builds_deduplicated_plan():
    health = {
        "overall_status": "DEGRADED",
        "components": {
            "execution": {
                "metrics": {},
            }
        },
        "recommended_actions": [
            {
                "severity": "HIGH",
                "category": (
                    "artifact_contract"
                ),
                "action_type": (
                    "REBUILD_REQUIRED_OUTPUTS"
                ),
                "target": (
                    "research_experiment_execution"
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
                    "research_experiment_designer"
                ),
            },
        ],
    }

    plan = build_remediation_plan(
        health
    )

    assert plan[
        "plan_status"
    ] == "READY"

    assert plan[
        "execution"
    ][
        "mode"
    ] == "EXECUTE"

    assert not plan[
        "execution"
    ][
        "authorized"
    ]

    jobs = [
        step["job_id"]
        for step in plan[
            "execution_steps"
        ]
    ]

    assert (
        "research_experiment_designer"
        in jobs
    )

    assert (
        "research_experiment_execution"
        in jobs
    )

    assert len(jobs) == len(
        set(jobs)
    )
