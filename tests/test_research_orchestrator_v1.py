"""Tests for Continuous Research Orchestrator v1."""

from __future__ import annotations

import pandas as pd
import pytest

from atlas.investment.research_orchestrator.planner import (
    build_execution_plan,
    classify_nonselected_jobs,
)
from atlas.investment.research_orchestrator.safety import (
    resolve_registered_command,
)


def schedule() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "job_id": "alpha_engines",
            "title": "Run Alpha Engines",
            "category": "alpha",
            "priority": "CRITICAL",
            "priority_rank": 1,
            "status": "READY",
            "reason": "Artifact is stale.",
            "command": (
                "python scripts/run_alpha_engines.py"
            ),
            "output_path": "alpha.json",
            "dependencies": "",
            "blocking_dependencies": "",
        },
        {
            "job_id": "regime_intelligence",
            "title": "Regime",
            "category": "market_context",
            "priority": "CRITICAL",
            "priority_rank": 1,
            "status": "BLOCKED",
            "reason": "Dependency stale.",
            "command": (
                "python scripts/"
                "update_regime_intelligence.py"
            ),
            "output_path": "regime.json",
            "dependencies": "alpha_engines",
            "blocking_dependencies": (
                "alpha_engines"
            ),
        },
        {
            "job_id": "macro_intelligence",
            "title": "Macro",
            "category": "market_context",
            "priority": "CRITICAL",
            "priority_rank": 1,
            "status": "CURRENT",
            "reason": "Current.",
            "command": (
                "python scripts/"
                "update_macro_intelligence.py"
            ),
            "output_path": "macro.json",
            "dependencies": "",
            "blocking_dependencies": "",
        },
    ])


def test_plan_selects_only_ready_jobs():
    plan = build_execution_plan(
        schedule(),
        execute=False,
        max_jobs=100,
    )

    assert plan[
        "job_id"
    ].tolist() == [
        "alpha_engines"
    ]


def test_dry_run_never_authorizes_execution():
    plan = build_execution_plan(
        schedule(),
        execute=False,
        max_jobs=100,
    )

    assert not plan[
        "execution_authorized"
    ].astype(bool).any()

    assert not plan[
        "execution_instruction"
    ].astype(bool).any()


def test_execute_flag_authorizes_registered_research_job():
    plan = build_execution_plan(
        schedule(),
        execute=True,
        max_jobs=100,
    )

    assert plan[
        "execution_authorized"
    ].astype(bool).all()

    assert not plan[
        "execution_instruction"
    ].astype(bool).any()


def test_max_jobs_is_respected():
    duplicated = pd.concat(
        [
            schedule(),
            schedule().assign(
                job_id="macro_intelligence",
                status="READY",
                command=(
                    "python scripts/"
                    "update_macro_intelligence.py"
                ),
            ),
        ],
        ignore_index=True,
    )

    plan = build_execution_plan(
        duplicated,
        execute=False,
        max_jobs=1,
    )

    assert len(plan) == 1


def test_blocked_and_skipped_classification():
    outputs = classify_nonselected_jobs(
        schedule()
    )

    assert (
        "regime_intelligence"
        in outputs[
            "blocked"
        ][
            "job_id"
        ].tolist()
    )

    assert (
        "macro_intelligence"
        in outputs[
            "skipped"
        ][
            "job_id"
        ].tolist()
    )


def test_registered_command_resolves_to_current_python():
    command = resolve_registered_command(
        "alpha_engines"
    )

    assert command[
        1
    ] == (
        "scripts/run_alpha_engines.py"
    )


def test_unregistered_job_is_rejected():
    with pytest.raises(
        ValueError
    ):
        resolve_registered_command(
            "not_a_real_job"
        )


def test_no_git_job_exists_in_registry():
    from atlas.investment.research_scheduler.registry import (
        JOBS,
    )

    for job in JOBS:
        assert "git " not in (
            job.command.lower()
        )


def test_no_live_execution_job_exists_in_registry():
    from atlas.investment.research_scheduler.registry import (
        JOBS,
    )

    for job in JOBS:
        assert "live_execution" not in (
            job.command.lower()
        )
