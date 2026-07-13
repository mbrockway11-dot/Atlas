"""Canonical job definitions for the Atlas investment scheduler."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class ScheduledJob:
    """One scheduler-controlled Atlas workflow."""

    name: str
    cadence_seconds: int
    session_name: str
    dependencies: tuple[str, ...] = ()
    enabled: bool = True
    paper_only: bool = True
    command: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        name = str(
            self.name
        ).strip().upper()

        session_name = str(
            self.session_name
        ).strip().upper()

        cadence = int(
            self.cadence_seconds
        )

        if not name:
            raise ValueError(
                "JOB_NAME_REQUIRED"
            )

        if cadence <= 0:
            raise ValueError(
                "JOB_CADENCE_MUST_BE_POSITIVE"
            )

        object.__setattr__(
            self,
            "name",
            name,
        )

        object.__setattr__(
            self,
            "session_name",
            session_name,
        )

        object.__setattr__(
            self,
            "cadence_seconds",
            cadence,
        )

        object.__setattr__(
            self,
            "dependencies",
            tuple(
                str(value)
                .strip()
                .upper()
                for value
                in self.dependencies
            ),
        )

        object.__setattr__(
            self,
            "command",
            tuple(
                str(value)
                for value
                in self.command
            ),
        )

    def to_dict(self) -> dict:
        return asdict(self)


DEFAULT_JOBS = (
    ScheduledJob(
        name=(
            "MARKET_DATA_REFRESH"
        ),
        cadence_seconds=60,
        session_name=(
            "CONTINUOUS"
        ),
        command=(
            "python",
            "scripts/build_coinbase_market_snapshot.py",
            "--symbols",
            "BTC-USD,ETH-USD,SOL-USD",
        ),
    ),
    ScheduledJob(
        name="SHADOW_PIPELINE",
        cadence_seconds=300,
        session_name=(
            "CONTINUOUS"
        ),
        dependencies=(
            "MARKET_DATA_REFRESH",
        ),
        command=(
            "python",
            "scripts/run_shadow_portfolio_pipeline.py",
        ),
    ),
    ScheduledJob(
        name=(
            "EXECUTION_ANALYTICS"
        ),
        cadence_seconds=300,
        session_name=(
            "CONTINUOUS"
        ),
        dependencies=(
            "SHADOW_PIPELINE",
        ),
        command=(
            "python",
            "scripts/build_execution_analytics.py",
        ),
    ),
    ScheduledJob(
        name=(
            "PERFORMANCE_LEDGER"
        ),
        cadence_seconds=300,
        session_name=(
            "CONTINUOUS"
        ),
        dependencies=(
            "EXECUTION_ANALYTICS",
        ),
        command=(
            "python",
            "scripts/record_shadow_performance.py",
        ),
    ),
    ScheduledJob(
        name="SYSTEM_AUDIT",
        cadence_seconds=900,
        session_name="ALWAYS",
        dependencies=(
            "PERFORMANCE_LEDGER",
        ),
        command=(
            "python",
            "scripts/audit_shadow_performance_ledger.py",
        ),
    ),
)


def validate_job_graph(
    jobs: Iterable[
        ScheduledJob
    ],
) -> dict[str, object]:
    """Validate job uniqueness, dependency order, and graph cycles."""
    rows = tuple(
        jobs
    )

    names = [
        job.name
        for job in rows
    ]

    indexes = {
        name: index
        for index, name
        in enumerate(names)
    }

    errors: list[str] = []

    if len(names) != len(
        set(names)
    ):
        errors.append(
            "DUPLICATE_JOB_NAME"
        )

    known = set(
        names
    )

    graph = {
        job.name: job.dependencies
        for job in rows
    }

    for job in rows:
        for dependency in (
            job.dependencies
        ):
            if dependency not in known:
                errors.append(
                    "UNKNOWN_DEPENDENCY:"
                    + job.name
                    + ":"
                    + dependency
                )

                continue

            if dependency == job.name:
                errors.append(
                    "SELF_DEPENDENCY:"
                    + job.name
                )

            if (
                dependency in indexes
                and indexes[dependency]
                > indexes[job.name]
            ):
                errors.append(
                    "DEPENDENCY_ORDER_INVALID:"
                    + job.name
                    + ":"
                    + dependency
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visiting:
            errors.append(
                "DEPENDENCY_CYCLE:"
                + name
            )

            return

        if name in visited:
            return

        visiting.add(
            name
        )

        for dependency in graph.get(
            name,
            (),
        ):
            if dependency in graph:
                visit(
                    dependency
                )

        visiting.remove(
            name
        )

        visited.add(
            name
        )

    for name in names:
        visit(
            name
        )

    return {
        "valid": not errors,
        "job_count": len(
            rows
        ),
        "errors": errors,
        "execution_order": names,
    }


__all__ = [
    "DEFAULT_JOBS",
    "ScheduledJob",
    "validate_job_graph",
]
