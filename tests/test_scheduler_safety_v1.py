"""Static safety tests for G.16 scheduling."""

from __future__ import annotations

from pathlib import Path


PACKAGE = Path(
    "src/atlas/investment/"
    "scheduling"
)


def test_scheduler_package_does_not_execute_orders():
    text = "\n".join(
        path.read_text(
            encoding="utf-8"
        )
        for path
        in PACKAGE.glob(
            "*.py"
        )
    )

    forbidden = [
        "run_paper_execution",
        "PaperBroker(",
        ".submit(",
        "place_order",
        "send_order",
        "write_paper_account",
        "api_secret",
        "private_key",
        "live_execution=True",
        "subprocess.run",
        "subprocess.Popen",
        "os.system",
    ]

    for value in forbidden:
        assert value not in text


def test_scheduler_declares_decision_only_contract():
    text = (
        PACKAGE
        / "scheduler.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        '"decision_only": True'
        in text
    )

    assert (
        '"commands_not_executed": True'
        in text
    )

    assert (
        '"submits_orders": False'
        in text
    )

    assert (
        '"mutates_account": False'
        in text
    )


def test_scheduler_jobs_are_paper_only():
    from atlas.investment.scheduling import (
        DEFAULT_JOBS,
    )

    assert all(
        job.paper_only
        for job in DEFAULT_JOBS
    )
