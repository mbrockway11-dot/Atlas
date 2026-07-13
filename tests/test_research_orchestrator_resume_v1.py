"""Tests for resumable dependency-aware research cycles."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from atlas.investment.research_orchestrator import cycle
from atlas.investment.research_orchestrator.resume import (
    completed_job_ids,
    is_resumable_state,
    load_resume_state,
    write_resume_state,
)


def test_resume_state_round_trip(tmp_path: Path):
    path = tmp_path / "state.json"

    written = write_resume_state(
        run_id="ORCH-1",
        status="FAILED",
        execute=True,
        started_at="2026-07-12T00:00:00+00:00",
        initial_state_hash="abc",
        results=[
            {
                "job_id": "alpha_engines",
                "status": "SUCCEEDED",
            },
            {
                "job_id": "macro_intelligence",
                "status": "FAILED",
            },
        ],
        path=path,
        failure_detected=True,
    )

    loaded = load_resume_state(path)

    assert loaded == written
    assert loaded["resumable"] is True
    assert completed_job_ids(loaded) == {
        "alpha_engines"
    }
    assert is_resumable_state(loaded)


def test_successful_state_is_not_resumable(tmp_path: Path):
    path = tmp_path / "state.json"

    write_resume_state(
        run_id="ORCH-2",
        status="SUCCEEDED",
        execute=True,
        started_at="2026-07-12T00:00:00+00:00",
        initial_state_hash="abc",
        results=[],
        path=path,
    )

    assert not is_resumable_state(
        load_resume_state(path)
    )


def test_malformed_resume_state_is_ignored(tmp_path: Path):
    path = tmp_path / "state.json"
    path.write_text("{broken", encoding="utf-8")

    assert load_resume_state(path) == {}


def test_resume_skips_completed_jobs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    schedule_path = tmp_path / "schedule.csv"

    pd.DataFrame([
        {
            "job_id": "alpha_engines",
            "title": "Alpha",
            "category": "alpha",
            "priority": "CRITICAL",
            "priority_rank": 1,
            "status": "READY",
            "reason": "stale",
            "command": (
                "python scripts/run_alpha_engines.py"
            ),
            "output_path": "alpha.json",
            "dependencies": "",
            "blocking_dependencies": "",
        },
        {
            "job_id": "macro_intelligence",
            "title": "Macro",
            "category": "macro",
            "priority": "CRITICAL",
            "priority_rank": 1,
            "status": "READY",
            "reason": "stale",
            "command": (
                "python scripts/"
                "update_macro_intelligence.py"
            ),
            "output_path": "macro.json",
            "dependencies": "",
            "blocking_dependencies": "",
        },
    ]).to_csv(schedule_path, index=False)

    monkeypatch.setattr(
        cycle,
        "build_research_scheduler_report",
        lambda: {
            "state_hash": "state-1",
            "outputs": {
                "research_schedule_csv": str(
                    schedule_path
                )
            },
        },
    )

    monkeypatch.setattr(
        cycle,
        "load_resume_state",
        lambda: {
            "run_id": "ORCH-EXISTING",
            "status": "FAILED",
            "execute": True,
            "started_at": (
                "2026-07-12T00:00:00+00:00"
            ),
            "completed_job_ids": [
                "alpha_engines"
            ],
            "results": [
                {
                    "job_id": "alpha_engines",
                    "status": "SUCCEEDED",
                }
            ],
        },
    )

    executed: list[str] = []

    def fake_execute_job(**kwargs):
        executed.append(kwargs["job_id"])
        return {
            "job_id": kwargs["job_id"],
            "status": "SUCCEEDED",
            "started_at": "",
            "completed_at": "",
            "duration_seconds": 0.0,
            "returncode": 0,
            "stdout_path": "",
            "stderr_path": "",
            "error": "",
        }

    monkeypatch.setattr(
        cycle,
        "execute_job",
        fake_execute_job,
    )

    checkpoints: list[dict] = []

    monkeypatch.setattr(
        cycle,
        "write_resume_state",
        lambda **kwargs: checkpoints.append(
            kwargs
        ) or kwargs,
    )

    result = cycle.run_research_cycle(
        execute=True,
        resume=True,
        max_jobs=10,
        self_heal=False,
    )

    assert result["run_id"] == "ORCH-EXISTING"
    assert result["resumed"] is True
    assert executed == ["macro_intelligence"]
    assert "alpha_engines" in (
        result["completed_job_ids"]
    )
    assert "macro_intelligence" in (
        result["completed_job_ids"]
    )
    assert checkpoints


def test_resume_requires_incomplete_checkpoint(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        cycle,
        "build_research_scheduler_report",
        lambda: {
            "state_hash": "state-1",
            "outputs": {
                "research_schedule_csv": "unused.csv"
            },
        },
    )

    monkeypatch.setattr(
        cycle,
        "load_resume_state",
        lambda: {},
    )

    with pytest.raises(
        ValueError,
        match="No resumable",
    ):
        cycle.run_research_cycle(
            execute=True,
            resume=True,
        )


def test_resume_and_restart_are_mutually_exclusive():
    with pytest.raises(
        ValueError,
        match="mutually exclusive",
    ):
        cycle.run_research_cycle(
            execute=True,
            resume=True,
            restart=True,
        )
