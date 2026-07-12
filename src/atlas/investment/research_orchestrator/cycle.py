"""Continuous Research Orchestrator cycle controller."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.research_orchestrator.executor import (
    execute_job,
)
from atlas.investment.research_orchestrator.planner import (
    build_execution_plan,
    classify_nonselected_jobs,
)
from atlas.investment.research_scheduler import (
    build_research_scheduler_report,
)


ROOT = Path(
    __file__
).resolve().parents[4]


def run_research_cycle(
    *,
    execute: bool = False,
    max_jobs: int = 100,
    timeout_seconds: int = 1800,
    continue_on_failure: bool = False,
) -> dict[str, Any]:
    """Run or preview one dependency-aware research cycle."""
    started_at = datetime.now(
        UTC
    )

    initial_scheduler = (
        build_research_scheduler_report()
    )

    run_id = build_run_id(
        state_hash=str(
            initial_scheduler[
                "state_hash"
            ]
        ),
        started_at=started_at,
        execute=execute,
    )

    current_schedule = pd.read_csv(
        initial_scheduler[
            "outputs"
        ][
            "research_schedule_csv"
        ]
    )

    initial_plan = build_execution_plan(
        current_schedule,
        execute=execute,
        max_jobs=max_jobs,
    )

    nonselected = (
        classify_nonselected_jobs(
            current_schedule
        )
    )

    results: list[dict[str, Any]] = []
    attempted_jobs: set[str] = set()
    failure_detected = False

    if not execute:
        for _, plan_row in (
            initial_plan.iterrows()
        ):
            results.append({
                "job_id": str(
                    plan_row["job_id"]
                ),
                "status": "DRY_RUN",
                "started_at": "",
                "completed_at": "",
                "duration_seconds": 0.0,
                "returncode": None,
                "stdout_path": "",
                "stderr_path": "",
                "error": "",
                "execution_authorized": False,
                "execution_instruction": False,
            })

    else:
        while (
            len(attempted_jobs)
            < max(
                0,
                int(max_jobs),
            )
        ):
            scheduler_report = (
                build_research_scheduler_report()
            )

            current_schedule = pd.read_csv(
                scheduler_report[
                    "outputs"
                ][
                    "research_schedule_csv"
                ]
            )

            plan = build_execution_plan(
                current_schedule,
                execute=True,
                max_jobs=max_jobs,
            )

            available = plan[
                ~plan[
                    "job_id"
                ].astype(str).isin(
                    attempted_jobs
                )
            ]

            if available.empty:
                break

            next_job_id = str(
                available.iloc[0][
                    "job_id"
                ]
            )

            attempted_jobs.add(
                next_job_id
            )

            result = execute_job(
                job_id=next_job_id,
                run_id=run_id,
                timeout_seconds=(
                    timeout_seconds
                ),
                root=ROOT,
            )

            results.append(result)

            if result["status"] not in {
                "SUCCEEDED",
            }:
                failure_detected = True

                if not continue_on_failure:
                    break

        final_scheduler = (
            build_research_scheduler_report()
        )

        current_schedule = pd.read_csv(
            final_scheduler[
                "outputs"
            ][
                "research_schedule_csv"
            ]
        )

        nonselected = (
            classify_nonselected_jobs(
                current_schedule
            )
        )

    completed_at = datetime.now(
        UTC
    )

    return {
        "run_id": run_id,
        "execute": execute,
        "started_at": (
            started_at.isoformat()
        ),
        "completed_at": (
            completed_at.isoformat()
        ),
        "duration_seconds": round(
            (
                completed_at
                - started_at
            ).total_seconds(),
            8,
        ),
        "initial_scheduler": (
            initial_scheduler
        ),
        "initial_plan": initial_plan,
        "results": pd.DataFrame(
            results
        ),
        "skipped": nonselected[
            "skipped"
        ],
        "blocked": nonselected[
            "blocked"
        ],
        "failure_detected": (
            failure_detected
        ),
    }


def build_run_id(
    *,
    state_hash: str,
    started_at: datetime,
    execute: bool,
) -> str:
    payload = json.dumps(
        {
            "state_hash": state_hash,
            "started_at": (
                started_at.isoformat()
            ),
            "execute": execute,
        },
        sort_keys=True,
    ).encode("utf-8")

    return (
        "ORCH-"
        + hashlib.sha256(
            payload
        ).hexdigest()[:20]
    )
