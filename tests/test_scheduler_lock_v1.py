"""Tests for the Atlas scheduler single-instance lock."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.investment.scheduling import (
    SchedulerLock,
)


def test_scheduler_lock_is_exclusive(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "scheduler.lock"
    )

    first = SchedulerLock(
        path
    )

    first.acquire()

    try:
        second = SchedulerLock(
            path
        )

        with pytest.raises(
            RuntimeError,
            match=(
                "SCHEDULER_ALREADY_RUNNING"
            ),
        ):
            second.acquire()

    finally:
        first.release()

    assert not path.exists()


def test_context_manager_releases_lock(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "scheduler.lock"
    )

    with SchedulerLock(
        path
    ):
        assert path.exists()

    assert not path.exists()
