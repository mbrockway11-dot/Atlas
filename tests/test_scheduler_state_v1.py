"""Tests for persistent scheduler state updates."""

from __future__ import annotations

import pytest

from atlas.investment.scheduling import (
    apply_job_results,
)


def test_success_updates_completion():
    decision = {
        "decision_id": "DECISION-1",
        "evaluated_at": (
            "2026-07-13T16:00:00+00:00"
        ),
        "due_jobs": [
            "REFRESH"
        ],
    }

    state = apply_job_results(
        state={
            "jobs": {},
        },
        decision=decision,
        results={
            "REFRESH": {
                "success": True,
                "result_id": (
                    "SNAPSHOT-1"
                ),
            }
        },
    )

    job = state["jobs"][
        "REFRESH"
    ]

    assert job[
        "last_status"
    ] == "SUCCESS"

    assert job[
        "last_completed_at"
    ] == decision[
        "evaluated_at"
    ]

    assert job[
        "attempt_count"
    ] == 1


def test_second_success_increments_attempt_count():
    decision = {
        "decision_id": "DECISION-2",
        "evaluated_at": (
            "2026-07-13T16:05:00+00:00"
        ),
        "due_jobs": [
            "REFRESH"
        ],
    }

    state = apply_job_results(
        state={
            "jobs": {
                "REFRESH": {
                    "attempt_count": 1,
                    "last_status": (
                        "SUCCESS"
                    ),
                    "last_completed_at": (
                        "2026-07-13T16:00:00+00:00"
                    ),
                }
            },
        },
        decision=decision,
        results={
            "REFRESH": {
                "success": True,
                "result_id": (
                    "SNAPSHOT-2"
                ),
            }
        },
    )

    assert state["jobs"][
        "REFRESH"
    ][
        "attempt_count"
    ] == 2


def test_failure_does_not_advance_completion():
    decision = {
        "decision_id": "DECISION-1",
        "evaluated_at": (
            "2026-07-13T16:00:00+00:00"
        ),
        "due_jobs": [
            "REFRESH"
        ],
    }

    state = apply_job_results(
        state={
            "jobs": {
                "REFRESH": {
                    "last_completed_at": (
                        "2026-07-13T15:00:00+00:00"
                    )
                }
            },
        },
        decision=decision,
        results={
            "REFRESH": {
                "success": False,
                "error": (
                    "PROVIDER_FAILED"
                ),
            }
        },
    )

    job = state["jobs"][
        "REFRESH"
    ]

    assert job[
        "last_completed_at"
    ] == (
        "2026-07-13T15:00:00+00:00"
    )

    assert job[
        "last_status"
    ] == "FAILED"

    assert job[
        "last_error"
    ] == "PROVIDER_FAILED"


def test_result_not_in_decision_fails():
    with pytest.raises(
        ValueError,
        match=(
            "JOB_RESULT_NOT_IN_DECISION"
        ),
    ):
        apply_job_results(
            state={
                "jobs": {},
            },
            decision={
                "decision_id": (
                    "DECISION-1"
                ),
                "evaluated_at": (
                    "2026-07-13T16:00:00+00:00"
                ),
                "due_jobs": [],
            },
            results={
                "REFRESH": {
                    "success": True,
                }
            },
        )
