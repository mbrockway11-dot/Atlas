"""Atlas Research Scheduler v1 orchestration."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from atlas.investment.research_scheduler.config import (
    ARTIFACT_FRESHNESS_CSV,
    BLOCKED_JOBS_CSV,
    COMPLETED_JOBS_CSV,
    DEPENDENCY_GRAPH_CSV,
    FAILED_JOBS_CSV,
    OUTPUT_DIR,
    PENDING_JOBS_CSV,
    REPORT_JSON,
    REPORT_MD,
    RESEARCH_SCHEDULE_CSV,
    RUN_HISTORY_CSV,
    SCHEDULER_STATE_JSON,
    SCHEMA_VERSION,
    VERSION,
)
from atlas.investment.research_scheduler.freshness import (
    inspect_all_artifacts,
)
from atlas.investment.research_scheduler.history import (
    append_run_history,
)
from atlas.investment.research_scheduler.scheduler import (
    build_dependency_graph,
    build_research_schedule,
)
from atlas.investment.state_api import (
    get_state_hash,
)


def build_research_scheduler_report() -> dict[str, Any]:
    """Evaluate the Atlas research agenda without executing it."""
    generated_at = datetime.now(
        UTC
    ).isoformat()

    state_hash = get_state_hash()

    freshness_rows = (
        inspect_all_artifacts()
    )

    freshness = pd.DataFrame(
        freshness_rows
    )

    schedule = build_research_schedule(
        freshness_rows
    )

    dependencies = (
        build_dependency_graph()
    )

    pending = schedule[
        schedule["status"].eq(
            "READY"
        )
    ].copy()

    blocked = schedule[
        schedule["status"].eq(
            "BLOCKED"
        )
    ].copy()

    failed = schedule[
        schedule["status"].isin(
            [
                "FAILED",
                "MISSING",
                "STALE",
            ]
        )
    ].copy()

    completed = schedule[
        schedule["status"].eq(
            "CURRENT"
        )
    ].copy()

    status_counts = (
        schedule[
            "status"
        ].value_counts().to_dict()
        if not schedule.empty
        else {}
    )

    scheduler_run_id = (
        build_scheduler_run_id(
            state_hash=state_hash,
            generated_at=generated_at,
            schedule=schedule,
        )
    )

    success = bool(
        status_counts.get(
            "FAILED",
            0,
        ) == 0
    )

    report = {
        "success": success,
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "scheduler_run_id": (
            scheduler_run_id
        ),
        "generated_at": generated_at,
        "state_hash": state_hash,
        "summary": (
            "Atlas Research Scheduler v1 evaluated "
            f"{len(schedule)} job(s), identified "
            f"{len(pending)} ready job(s), "
            f"{len(blocked)} blocked job(s), and "
            f"{len(completed)} current job(s)."
        ),
        "counts": {
            "total_jobs": int(
                len(schedule)
            ),
            "current_jobs": int(
                status_counts.get(
                    "CURRENT",
                    0,
                )
            ),
            "ready_jobs": int(
                status_counts.get(
                    "READY",
                    0,
                )
            ),
            "blocked_jobs": int(
                status_counts.get(
                    "BLOCKED",
                    0,
                )
            ),
            "failed_jobs": int(
                status_counts.get(
                    "FAILED",
                    0,
                )
            ),
            "missing_jobs": int(
                status_counts.get(
                    "MISSING",
                    0,
                )
            ),
            "stale_jobs": int(
                status_counts.get(
                    "STALE",
                    0,
                )
            ),
            "disabled_jobs": int(
                status_counts.get(
                    "DISABLED",
                    0,
                )
            ),
        },
        "status_counts": status_counts,
        "next_jobs": (
            pending.head(10).to_dict(
                orient="records"
            )
        ),
        "blocked_job_preview": (
            blocked.head(10).to_dict(
                orient="records"
            )
        ),
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "executes_jobs": False,
            "changes_artifacts": False,
            "changes_engine_code": False,
            "changes_engine_registry": False,
            "changes_portfolio": False,
            "changes_manual_decisions": False,
            "commands_are_advisory_only": True,
            "dependency_aware": True,
            "deterministic_given_artifacts_and_time": True,
        },
        "outputs": {
            "research_schedule_csv": str(
                RESEARCH_SCHEDULE_CSV
            ),
            "pending_jobs_csv": str(
                PENDING_JOBS_CSV
            ),
            "blocked_jobs_csv": str(
                BLOCKED_JOBS_CSV
            ),
            "completed_jobs_csv": str(
                COMPLETED_JOBS_CSV
            ),
            "failed_jobs_csv": str(
                FAILED_JOBS_CSV
            ),
            "artifact_freshness_csv": str(
                ARTIFACT_FRESHNESS_CSV
            ),
            "dependency_graph_csv": str(
                DEPENDENCY_GRAPH_CSV
            ),
            "run_history_csv": str(
                RUN_HISTORY_CSV
            ),
            "scheduler_state_json": str(
                SCHEDULER_STATE_JSON
            ),
            "report_json": str(
                REPORT_JSON
            ),
            "report_markdown": str(
                REPORT_MD
            ),
        },
    }

    write_outputs(
        report=report,
        schedule=schedule,
        pending=pending,
        blocked=blocked,
        completed=completed,
        failed=failed,
        freshness=freshness,
        dependencies=dependencies,
    )

    return report


def build_scheduler_run_id(
    *,
    state_hash: str,
    generated_at: str,
    schedule: pd.DataFrame,
) -> str:
    payload = {
        "state_hash": state_hash,
        "generated_at": generated_at,
        "status": (
            schedule[
                [
                    "job_id",
                    "status",
                ]
            ].to_dict(
                orient="records"
            )
        ),
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
    ).encode("utf-8")

    return (
        "SCHED-"
        + hashlib.sha256(
            encoded
        ).hexdigest()[:20]
    )


def write_outputs(
    *,
    report: dict,
    schedule: pd.DataFrame,
    pending: pd.DataFrame,
    blocked: pd.DataFrame,
    completed: pd.DataFrame,
    failed: pd.DataFrame,
    freshness: pd.DataFrame,
    dependencies: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    schedule.to_csv(
        RESEARCH_SCHEDULE_CSV,
        index=False,
    )

    pending.to_csv(
        PENDING_JOBS_CSV,
        index=False,
    )

    blocked.to_csv(
        BLOCKED_JOBS_CSV,
        index=False,
    )

    completed.to_csv(
        COMPLETED_JOBS_CSV,
        index=False,
    )

    failed.to_csv(
        FAILED_JOBS_CSV,
        index=False,
    )

    freshness.to_csv(
        ARTIFACT_FRESHNESS_CSV,
        index=False,
    )

    dependencies.to_csv(
        DEPENDENCY_GRAPH_CSV,
        index=False,
    )

    history = pd.DataFrame()

    if (
        RUN_HISTORY_CSV.exists()
        and RUN_HISTORY_CSV.stat().st_size > 0
    ):
        try:
            history = pd.read_csv(
                RUN_HISTORY_CSV
            )
        except (
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
            OSError,
        ):
            history = pd.DataFrame()

    history_row = {
        "scheduler_run_id": report[
            "scheduler_run_id"
        ],
        "generated_at": report[
            "generated_at"
        ],
        "state_hash": report[
            "state_hash"
        ],
        "total_jobs": report[
            "counts"
        ][
            "total_jobs"
        ],
        "current_jobs": report[
            "counts"
        ][
            "current_jobs"
        ],
        "ready_jobs": report[
            "counts"
        ][
            "ready_jobs"
        ],
        "blocked_jobs": report[
            "counts"
        ][
            "blocked_jobs"
        ],
        "failed_jobs": report[
            "counts"
        ][
            "failed_jobs"
        ],
        "missing_jobs": report[
            "counts"
        ][
            "missing_jobs"
        ],
        "stale_jobs": report[
            "counts"
        ][
            "stale_jobs"
        ],
        "success": report[
            "success"
        ],
    }

    history = append_run_history(
        existing=history,
        row=history_row,
    )

    history.to_csv(
        RUN_HISTORY_CSV,
        index=False,
    )

    scheduler_state = {
        "version": report["version"],
        "schema_version": report[
            "schema_version"
        ],
        "scheduler_run_id": report[
            "scheduler_run_id"
        ],
        "generated_at": report[
            "generated_at"
        ],
        "state_hash": report[
            "state_hash"
        ],
        "counts": report["counts"],
        "next_jobs": report[
            "next_jobs"
        ],
        "blocked_jobs": report[
            "blocked_job_preview"
        ],
        "contract": report[
            "contract"
        ],
    }

    SCHEDULER_STATE_JSON.write_text(
        json.dumps(
            scheduler_state,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    REPORT_JSON.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    REPORT_MD.write_text(
        build_markdown(
            report
        ),
        encoding="utf-8",
    )


def build_markdown(
    report: dict,
) -> str:
    lines = [
        "# Atlas Research Scheduler v1",
        "",
        report["summary"],
        "",
        (
            f"- State hash: "
            f"`{report['state_hash']}`"
        ),
        (
            f"- Current jobs: "
            f"`{report['counts']['current_jobs']}`"
        ),
        (
            f"- Ready jobs: "
            f"`{report['counts']['ready_jobs']}`"
        ),
        (
            f"- Blocked jobs: "
            f"`{report['counts']['blocked_jobs']}`"
        ),
        (
            f"- Failed jobs: "
            f"`{report['counts']['failed_jobs']}`"
        ),
        "",
        "## Next Research Jobs",
        "",
    ]

    next_jobs = report.get(
        "next_jobs",
        [],
    )

    if not next_jobs:
        lines.extend([
            "_No jobs currently require attention._",
            "",
        ])
    else:
        for job in next_jobs:
            lines.extend([
                (
                    f"### {job.get('schedule_rank')} - "
                    f"{job.get('title')}"
                ),
                "",
                (
                    f"- Job: "
                    f"`{job.get('job_id')}`"
                ),
                (
                    f"- Priority: "
                    f"`{job.get('priority')}`"
                ),
                (
                    f"- Status: "
                    f"`{job.get('status')}`"
                ),
                (
                    f"- Reason: "
                    f"{job.get('reason')}"
                ),
                (
                    f"- Advisory command: "
                    f"`{job.get('command')}`"
                ),
                (
                    "- Execution authorized: "
                    f"`{job.get('execution_authorized')}`"
                ),
                "",
            ])

    lines.extend([
        "## Contract",
        "",
        "```json",
        json.dumps(
            report["contract"],
            indent=2,
        ),
        "```",
        "",
    ])

    return "\n".join(lines)
