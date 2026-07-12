"""Continuous Research Orchestrator planning."""

from __future__ import annotations

from typing import Any

import pandas as pd

from atlas.investment.research_orchestrator.safety import (
    resolve_registered_command,
)
from atlas.investment.research_scheduler.scheduler import (
    topological_order,
)


PLAN_COLUMNS = [
    "plan_rank",
    "dependency_order",
    "job_id",
    "title",
    "category",
    "priority",
    "scheduler_status",
    "reason",
    "command",
    "resolved_command",
    "dependencies",
    "blocking_dependencies",
    "selected_for_execution",
    "execution_authorized",
    "execution_instruction",
]


def build_execution_plan(
    schedule: pd.DataFrame,
    *,
    execute: bool,
    max_jobs: int,
) -> pd.DataFrame:
    """Build a safe execution plan from scheduler output."""
    if schedule is None or schedule.empty:
        return pd.DataFrame(
            columns=PLAN_COLUMNS
        )

    dependency_order = {
        job_id: index
        for index, job_id in enumerate(
            topological_order(),
            start=1,
        )
    }

    rows: list[dict[str, Any]] = []

    ready = schedule[
        schedule[
            "status"
        ].astype(str).eq("READY")
    ].copy()

    ready[
        "dependency_order"
    ] = ready[
        "job_id"
    ].map(
        dependency_order
    )

    ready = ready.sort_values(
        [
            "dependency_order",
            "priority_rank",
            "job_id",
        ],
        kind="stable",
    ).head(
        max(
            0,
            int(max_jobs),
        )
    )

    for _, source in ready.iterrows():
        job_id = str(
            source["job_id"]
        )

        resolved = resolve_registered_command(
            job_id
        )

        rows.append({
            "dependency_order": int(
                dependency_order[
                    job_id
                ]
            ),
            "job_id": job_id,
            "title": str(
                source.get(
                    "title",
                    job_id,
                )
            ),
            "category": str(
                source.get(
                    "category",
                    "",
                )
            ),
            "priority": str(
                source.get(
                    "priority",
                    "",
                )
            ),
            "scheduler_status": str(
                source.get(
                    "status",
                    "",
                )
            ),
            "reason": str(
                source.get(
                    "reason",
                    "",
                )
            ),
            "command": str(
                source.get(
                    "command",
                    "",
                )
            ),
            "resolved_command": " ".join(
                resolved
            ),
            "dependencies": str(
                source.get(
                    "dependencies",
                    "",
                )
            ),
            "blocking_dependencies": str(
                source.get(
                    "blocking_dependencies",
                    "",
                )
            ),
            "selected_for_execution": True,
            "execution_authorized": bool(
                execute
            ),
            "execution_instruction": False,
        })

    frame = pd.DataFrame(
        rows
    )

    if frame.empty:
        return pd.DataFrame(
            columns=PLAN_COLUMNS
        )

    frame.insert(
        0,
        "plan_rank",
        range(
            1,
            len(frame) + 1,
        ),
    )

    return frame[
        PLAN_COLUMNS
    ]


def classify_nonselected_jobs(
    schedule: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Separate current, blocked, and otherwise skipped jobs."""
    if schedule is None or schedule.empty:
        empty = pd.DataFrame()

        return {
            "skipped": empty,
            "blocked": empty,
        }

    blocked = schedule[
        schedule[
            "status"
        ].astype(str).eq("BLOCKED")
    ].copy()

    skipped = schedule[
        ~schedule[
            "status"
        ].astype(str).isin([
            "READY",
            "BLOCKED",
        ])
    ].copy()

    return {
        "skipped": skipped,
        "blocked": blocked,
    }
