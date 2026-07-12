"""Continuous Research Orchestrator reporting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.research_orchestrator.config import (
    BLOCKED_JOBS_CSV,
    EXECUTED_JOBS_CSV,
    EXECUTION_GRAPH_CSV,
    EXECUTION_PLAN_CSV,
    EXECUTION_STATE_JSON,
    EXECUTION_TIMELINE_CSV,
    FAILED_JOBS_CSV,
    OUTPUT_DIR,
    REPORT_JSON,
    REPORT_MD,
    RUN_HISTORY_CSV,
    SCHEMA_VERSION,
    SKIPPED_JOBS_CSV,
    VERSION,
)
from atlas.investment.research_orchestrator.cycle import (
    run_research_cycle,
)
from atlas.investment.research_scheduler.scheduler import (
    build_dependency_graph,
)


def build_orchestrator_report(
    *,
    execute: bool = False,
    max_jobs: int = 100,
    timeout_seconds: int = 1800,
    continue_on_failure: bool = False,
    resume: bool = False,
    restart: bool = False,
) -> dict[str, Any]:
    """Build and optionally execute one research cycle."""
    cycle = run_research_cycle(
        execute=execute,
        max_jobs=max_jobs,
        timeout_seconds=(
            timeout_seconds
        ),
        continue_on_failure=(
            continue_on_failure
        ),
        resume=resume,
        restart=restart,
    )

    results = cycle["results"]

    succeeded = filter_status(
        results,
        "SUCCEEDED",
    )

    dry_run = filter_status(
        results,
        "DRY_RUN",
    )

    failed = results[
        results[
            "status"
        ].astype(str).isin([
            "FAILED",
            "TIMED_OUT",
        ])
    ].copy() if not results.empty else pd.DataFrame()

    success = not bool(
        cycle["failure_detected"]
    )

    report = {
        "success": success,
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "run_id": cycle[
            "run_id"
        ],
        "mode": (
            "EXECUTE"
            if execute
            else "DRY_RUN"
        ),
        "started_at": cycle[
            "started_at"
        ],
        "completed_at": cycle[
            "completed_at"
        ],
        "duration_seconds": cycle[
            "duration_seconds"
        ],
        "resumed": bool(
            cycle.get("resumed", False)
        ),
        "restarted": bool(
            cycle.get("restarted", False)
        ),
        "resumed_from_run_id": str(
            cycle.get(
                "resumed_from_run_id",
                "",
            )
        ),
        "completed_job_ids": list(
            cycle.get(
                "completed_job_ids",
                [],
            )
        ),
        "attempted_this_invocation": list(
            cycle.get(
                "attempted_this_invocation",
                [],
            )
        ),
        "initial_state_hash": cycle[
            "initial_scheduler"
        ][
            "state_hash"
        ],
        "summary": (
            "Continuous Research Orchestrator v1 "
            f"planned {len(cycle['initial_plan'])} job(s), "
            f"executed {len(succeeded)} successfully, "
            f"previewed {len(dry_run)}, and "
            f"recorded {len(failed)} failure(s)."
        ),
        "counts": {
            "planned_jobs": int(
                len(
                    cycle[
                        "initial_plan"
                    ]
                )
            ),
            "successful_jobs": int(
                len(succeeded)
            ),
            "dry_run_jobs": int(
                len(dry_run)
            ),
            "failed_jobs": int(
                len(failed)
            ),
            "skipped_jobs": int(
                len(
                    cycle[
                        "skipped"
                    ]
                )
            ),
            "blocked_jobs": int(
                len(
                    cycle[
                        "blocked"
                    ]
                )
            ),
        },
        "contract": {
            "research_only": True,
            "trading_execution": False,
            "broker_connectivity": False,
            "git_operations": False,
            "code_modification": False,
            "production_deployment": False,
            "dry_run_default": True,
            "explicit_execute_flag_required": True,
            "registered_commands_only": True,
            "dependency_aware": True,
            "scheduler_refreshed_after_each_job": True,
            "fail_fast_default": True,
            "resume_supported": True,
            "restart_supported": True,
            "atomic_job_checkpoints": True,
            "completed_jobs_skipped_on_resume": True,
        },
        "outputs": {
            "execution_plan_csv": str(
                EXECUTION_PLAN_CSV
            ),
            "executed_jobs_csv": str(
                EXECUTED_JOBS_CSV
            ),
            "skipped_jobs_csv": str(
                SKIPPED_JOBS_CSV
            ),
            "blocked_jobs_csv": str(
                BLOCKED_JOBS_CSV
            ),
            "failed_jobs_csv": str(
                FAILED_JOBS_CSV
            ),
            "timeline_csv": str(
                EXECUTION_TIMELINE_CSV
            ),
            "graph_csv": str(
                EXECUTION_GRAPH_CSV
            ),
            "run_history_csv": str(
                RUN_HISTORY_CSV
            ),
            "execution_state_json": str(
                EXECUTION_STATE_JSON
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
        cycle=cycle,
        failed=failed,
    )

    return report


def filter_status(
    frame: pd.DataFrame,
    status: str,
) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()

    return frame[
        frame[
            "status"
        ].astype(str).eq(
            status
        )
    ].copy()


def write_outputs(
    *,
    report: dict,
    cycle: dict,
    failed: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    cycle[
        "initial_plan"
    ].to_csv(
        EXECUTION_PLAN_CSV,
        index=False,
    )

    cycle[
        "results"
    ].to_csv(
        EXECUTED_JOBS_CSV,
        index=False,
    )

    cycle[
        "skipped"
    ].to_csv(
        SKIPPED_JOBS_CSV,
        index=False,
    )

    cycle[
        "blocked"
    ].to_csv(
        BLOCKED_JOBS_CSV,
        index=False,
    )

    failed.to_csv(
        FAILED_JOBS_CSV,
        index=False,
    )

    timeline = cycle[
        "results"
    ].copy()

    timeline.to_csv(
        EXECUTION_TIMELINE_CSV,
        index=False,
    )

    build_dependency_graph().to_csv(
        EXECUTION_GRAPH_CSV,
        index=False,
    )

    append_run_history(
        report
    )

    # execution_state.json is written atomically by the cycle controller.

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


def append_run_history(
    report: dict,
) -> None:
    existing = pd.DataFrame()

    if (
        RUN_HISTORY_CSV.exists()
        and RUN_HISTORY_CSV.stat().st_size > 0
    ):
        try:
            existing = pd.read_csv(
                RUN_HISTORY_CSV
            )
        except (
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
            OSError,
        ):
            existing = pd.DataFrame()

    row = {
        "run_id": report[
            "run_id"
        ],
        "mode": report[
            "mode"
        ],
        "started_at": report[
            "started_at"
        ],
        "completed_at": report[
            "completed_at"
        ],
        "duration_seconds": report[
            "duration_seconds"
        ],
        "initial_state_hash": report[
            "initial_state_hash"
        ],
        "planned_jobs": report[
            "counts"
        ][
            "planned_jobs"
        ],
        "successful_jobs": report[
            "counts"
        ][
            "successful_jobs"
        ],
        "dry_run_jobs": report[
            "counts"
        ][
            "dry_run_jobs"
        ],
        "failed_jobs": report[
            "counts"
        ][
            "failed_jobs"
        ],
        "success": report[
            "success"
        ],
    }

    history = pd.concat(
        [
            existing,
            pd.DataFrame([
                row
            ]),
        ],
        ignore_index=True,
    ).drop_duplicates(
        subset=["run_id"],
        keep="last",
    )

    history.to_csv(
        RUN_HISTORY_CSV,
        index=False,
    )


def build_markdown(
    report: dict,
) -> str:
    return "\n".join([
        "# Continuous Research Orchestrator v1",
        "",
        report["summary"],
        "",
        f"- Mode: `{report['mode']}`",
        f"- Success: `{report['success']}`",
        f"- Run ID: `{report['run_id']}`",
        (
            f"- Initial state hash: "
            f"`{report['initial_state_hash']}`"
        ),
        (
            f"- Planned jobs: "
            f"`{report['counts']['planned_jobs']}`"
        ),
        (
            f"- Successful jobs: "
            f"`{report['counts']['successful_jobs']}`"
        ),
        (
            f"- Dry-run jobs: "
            f"`{report['counts']['dry_run_jobs']}`"
        ),
        (
            f"- Failed jobs: "
            f"`{report['counts']['failed_jobs']}`"
        ),
        "",
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
