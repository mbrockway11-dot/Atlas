"""Tests for Atlas Research Scheduler v1."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from atlas.investment.research_scheduler.scheduler import (
    build_dependency_graph,
    build_research_schedule,
    topological_order,
)


def current_row(
    job_id: str,
) -> dict:
    return {
        "job_id": job_id,
        "title": job_id,
        "category": "test",
        "output_path": f"{job_id}.json",
        "exists": True,
        "valid": True,
        "modified_at": (
            "2026-07-12T00:00:00+00:00"
        ),
        "age_hours": 1.0,
        "stale_after_hours": 26.0,
        "fresh": True,
        "artifact_success": True,
        "artifact_version": "v1",
        "error": "",
    }


def all_current_rows() -> list[dict]:
    from atlas.investment.research_scheduler.registry import (
        JOBS,
    )

    return [
        current_row(
            job.job_id
        )
        for job in JOBS
    ]


def test_dependency_graph_is_acyclic():
    ordered = topological_order()

    assert len(ordered) > 10

    assert len(ordered) == len(
        set(ordered)
    )


def test_alpha_engines_precedes_regime():
    ordered = topological_order()

    assert ordered.index(
        "alpha_engines"
    ) < ordered.index(
        "regime_intelligence"
    )


def test_compiler_precedes_state_api():
    ordered = topological_order()

    assert ordered.index(
        "atlas_compiler"
    ) < ordered.index(
        "atlas_state_api"
    )


def test_all_current_artifacts_produce_current_jobs():
    schedule = build_research_schedule(
        all_current_rows()
    )

    assert set(
        schedule["status"]
    ) == {"CURRENT"}


def test_missing_root_job_becomes_ready():
    rows = all_current_rows()

    for row in rows:
        if (
            row["job_id"]
            == "alpha_engines"
        ):
            row["exists"] = False
            row["valid"] = False
            row["fresh"] = False
            row["error"] = (
                "ARTIFACT_NOT_FOUND"
            )

    schedule = build_research_schedule(
        rows
    ).set_index("job_id")

    assert (
        schedule.loc[
            "alpha_engines",
            "status",
        ]
        == "READY"
    )


def test_downstream_job_blocks_when_dependency_is_missing():
    rows = all_current_rows()

    for row in rows:
        if (
            row["job_id"]
            == "alpha_engines"
        ):
            row["exists"] = False
            row["valid"] = False
            row["fresh"] = False
            row["error"] = (
                "ARTIFACT_NOT_FOUND"
            )

        if (
            row["job_id"]
            == "regime_intelligence"
        ):
            row["fresh"] = False
            row["age_hours"] = 50.0

    schedule = build_research_schedule(
        rows
    ).set_index("job_id")

    assert (
        schedule.loc[
            "regime_intelligence",
            "status",
        ]
        == "BLOCKED"
    )

    assert (
        "alpha_engines"
        in schedule.loc[
            "regime_intelligence",
            "blocking_dependencies",
        ]
    )


def test_stale_job_with_current_dependencies_is_ready():
    rows = all_current_rows()

    for row in rows:
        if (
            row["job_id"]
            == "portfolio_optimizer"
        ):
            row["fresh"] = False
            row["age_hours"] = 50.0

    schedule = build_research_schedule(
        rows
    ).set_index("job_id")

    assert (
        schedule.loc[
            "portfolio_optimizer",
            "status",
        ]
        == "READY"
    )


def test_schedule_never_authorizes_execution():
    schedule = build_research_schedule(
        all_current_rows()
    )

    assert not schedule[
        "execution_authorized"
    ].astype(bool).any()

    assert not schedule[
        "execution_instruction"
    ].astype(bool).any()


def test_dependency_graph_contains_compiler_edge():
    graph = build_dependency_graph()

    matching = graph[
        graph[
            "downstream_job_id"
        ].eq(
            "atlas_state_api"
        )
    ]

    assert (
        "atlas_compiler"
        in set(
            matching[
                "upstream_job_id"
            ]
        )
    )
