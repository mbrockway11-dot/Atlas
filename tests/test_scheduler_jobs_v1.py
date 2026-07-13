"""Tests for Atlas scheduler job-graph validation."""

from __future__ import annotations

from atlas.investment.scheduling import (
    DEFAULT_JOBS,
    ScheduledJob,
    validate_job_graph,
)


def test_default_job_graph_is_valid():
    result = validate_job_graph(
        DEFAULT_JOBS
    )

    assert result["valid"]
    assert result["job_count"] == 5

    assert result[
        "execution_order"
    ] == [
        "MARKET_DATA_REFRESH",
        "SHADOW_PIPELINE",
        "EXECUTION_ANALYTICS",
        "PERFORMANCE_LEDGER",
        "SYSTEM_AUDIT",
    ]


def test_unknown_dependency_fails():
    result = validate_job_graph([
        ScheduledJob(
            name="A",
            cadence_seconds=60,
            session_name=(
                "CONTINUOUS"
            ),
            dependencies=(
                "MISSING",
            ),
        )
    ])

    assert not result["valid"]

    assert any(
        error.startswith(
            "UNKNOWN_DEPENDENCY"
        )
        for error
        in result["errors"]
    )


def test_dependency_order_fails_closed():
    result = validate_job_graph([
        ScheduledJob(
            name="B",
            cadence_seconds=60,
            session_name=(
                "CONTINUOUS"
            ),
            dependencies=(
                "A",
            ),
        ),
        ScheduledJob(
            name="A",
            cadence_seconds=60,
            session_name=(
                "CONTINUOUS"
            ),
        ),
    ])

    assert not result["valid"]

    assert any(
        error.startswith(
            "DEPENDENCY_ORDER_INVALID"
        )
        for error
        in result["errors"]
    )


def test_duplicate_job_name_fails():
    result = validate_job_graph([
        ScheduledJob(
            name="A",
            cadence_seconds=60,
            session_name=(
                "CONTINUOUS"
            ),
        ),
        ScheduledJob(
            name="A",
            cadence_seconds=120,
            session_name=(
                "ALWAYS"
            ),
        ),
    ])

    assert not result["valid"]

    assert (
        "DUPLICATE_JOB_NAME"
        in result["errors"]
    )


def test_nonpositive_cadence_fails():
    try:
        ScheduledJob(
            name="A",
            cadence_seconds=0,
            session_name=(
                "CONTINUOUS"
            ),
        )

    except ValueError as error:
        assert (
            "JOB_CADENCE_MUST_BE_POSITIVE"
            in str(error)
        )

    else:
        raise AssertionError(
            "Expected cadence failure"
        )
