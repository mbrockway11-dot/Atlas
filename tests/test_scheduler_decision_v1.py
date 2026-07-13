"""Tests for deterministic scheduler decisions."""

from __future__ import annotations

from datetime import UTC, datetime

from atlas.investment.scheduling import (
    ScheduledJob,
    evaluate_scheduler,
)


NOW = datetime(
    2026,
    7,
    13,
    16,
    0,
    tzinfo=UTC,
)


def test_new_job_is_due():
    decision = evaluate_scheduler(
        jobs=[
            ScheduledJob(
                name="REFRESH",
                cadence_seconds=60,
                session_name=(
                    "CONTINUOUS"
                ),
            )
        ],
        state={
            "jobs": {},
        },
        now=NOW,
    )

    assert decision["due_jobs"] == [
        "REFRESH"
    ]

    assert decision[
        "decisions"
    ][0][
        "reasons"
    ] == []


def test_recent_job_is_not_due():
    decision = evaluate_scheduler(
        jobs=[
            ScheduledJob(
                name="REFRESH",
                cadence_seconds=60,
                session_name=(
                    "CONTINUOUS"
                ),
            )
        ],
        state={
            "jobs": {
                "REFRESH": {
                    "last_status": (
                        "SUCCESS"
                    ),
                    "last_completed_at": (
                        "2026-07-13T15:59:30+00:00"
                    ),
                }
            }
        },
        now=NOW,
    )

    assert decision["due_jobs"] == []

    assert (
        "CADENCE_NOT_DUE"
        in decision[
            "decisions"
        ][0][
            "reasons"
        ]
    )


def test_dependency_chain_is_planned_in_order():
    jobs = [
        ScheduledJob(
            name="A",
            cadence_seconds=60,
            session_name=(
                "CONTINUOUS"
            ),
            command=(
                "python",
                "a.py",
            ),
        ),
        ScheduledJob(
            name="B",
            cadence_seconds=60,
            session_name=(
                "CONTINUOUS"
            ),
            dependencies=(
                "A",
            ),
            command=(
                "python",
                "b.py",
            ),
        ),
    ]

    decision = evaluate_scheduler(
        jobs=jobs,
        state={
            "jobs": {},
        },
        now=NOW,
    )

    assert decision["due_jobs"] == [
        "A",
        "B",
    ]

    assert [
        row["name"]
        for row
        in decision[
            "execution_plan"
        ]
    ] == [
        "A",
        "B",
    ]


def test_disabled_job_is_not_due():
    decision = evaluate_scheduler(
        jobs=[
            ScheduledJob(
                name="A",
                cadence_seconds=60,
                session_name=(
                    "CONTINUOUS"
                ),
                enabled=False,
            )
        ],
        state={
            "jobs": {},
        },
        now=NOW,
    )

    assert decision["due_jobs"] == []

    assert (
        "JOB_DISABLED"
        in decision[
            "decisions"
        ][0][
            "reasons"
        ]
    )


def test_closed_session_blocks_job():
    decision = evaluate_scheduler(
        jobs=[
            ScheduledJob(
                name="EQUITY_JOB",
                cadence_seconds=60,
                session_name=(
                    "US_EQUITIES"
                ),
            )
        ],
        state={
            "jobs": {},
        },
        now=datetime(
            2026,
            7,
            11,
            14,
            0,
            tzinfo=UTC,
        ),
    )

    assert decision["due_jobs"] == []

    assert any(
        reason.startswith(
            "SESSION_CLOSED"
        )
        for reason
        in decision[
            "decisions"
        ][0][
            "reasons"
        ]
    )


def test_scheduler_is_decision_only():
    decision = evaluate_scheduler(
        jobs=[
            ScheduledJob(
                name="A",
                cadence_seconds=60,
                session_name=(
                    "CONTINUOUS"
                ),
                command=(
                    "python",
                    "example.py",
                ),
            )
        ],
        state={
            "jobs": {},
        },
        now=NOW,
    )

    assert decision[
        "contract"
    ][
        "decision_only"
    ]

    assert decision[
        "contract"
    ][
        "commands_not_executed"
    ]

    assert not decision[
        "contract"
    ][
        "live_execution"
    ]
