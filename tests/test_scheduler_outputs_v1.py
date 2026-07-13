"""Tests for scheduler decision and history persistence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from atlas.investment.scheduling import (
    ScheduledJob,
    evaluate_scheduler,
    write_scheduler_outputs,
)


def test_scheduler_outputs_are_persistent(
    tmp_path: Path,
):
    decision = evaluate_scheduler(
        jobs=[
            ScheduledJob(
                name="A",
                cadence_seconds=60,
                session_name=(
                    "CONTINUOUS"
                ),
            )
        ],
        state={
            "jobs": {},
        },
        now=datetime(
            2026,
            7,
            13,
            16,
            0,
            tzinfo=UTC,
        ),
    )

    decision_path = (
        tmp_path
        / "decision.json"
    )

    state_path = (
        tmp_path
        / "state.json"
    )

    history_path = (
        tmp_path
        / "history.jsonl"
    )

    write_scheduler_outputs(
        decision=decision,
        state={
            "jobs": {},
        },
        decision_path=(
            decision_path
        ),
        state_path=(
            state_path
        ),
        history_path=(
            history_path
        ),
    )

    assert decision_path.exists()
    assert state_path.exists()
    assert history_path.exists()

    payload = json.loads(
        decision_path.read_text(
            encoding="utf-8"
        )
    )

    assert payload[
        "decision_id"
    ] == decision[
        "decision_id"
    ]

    history = [
        json.loads(line)
        for line
        in history_path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert len(history) == 1

    assert history[0][
        "decision_id"
    ] == decision[
        "decision_id"
    ]


def test_history_is_append_only(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "history.jsonl"
    )

    decision = evaluate_scheduler(
        jobs=[
            ScheduledJob(
                name="A",
                cadence_seconds=60,
                session_name=(
                    "CONTINUOUS"
                ),
            )
        ],
        state={
            "jobs": {},
        },
        now=datetime(
            2026,
            7,
            13,
            16,
            0,
            tzinfo=UTC,
        ),
    )

    for _ in range(2):
        write_scheduler_outputs(
            decision=decision,
            decision_path=(
                tmp_path
                / "decision.json"
            ),
            history_path=path,
        )

    rows = [
        line
        for line
        in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert len(rows) == 2
