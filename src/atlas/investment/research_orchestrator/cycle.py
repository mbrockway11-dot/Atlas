"""Continuous Research Orchestrator cycle controller."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.research_orchestrator.build_cache import (
    evaluate_build_cache,
    record_successful_build,
)
from atlas.investment.research_orchestrator.executor import (
    execute_job,
)
from atlas.investment.research_orchestrator.planner import (
    build_execution_plan,
    classify_nonselected_jobs,
)
from atlas.investment.research_orchestrator.provenance import (
    record_execution_provenance,
)
from atlas.investment.research_orchestrator.resume import (
    completed_job_ids,
    is_resumable_state,
    load_resume_state,
    write_resume_state,
)
from atlas.investment.research_orchestrator.self_healing import (
    annotate_recovery_result,
    blocked_job_ids,
    can_retry,
    schedule_signature,
    verify_job_health,
)
from atlas.investment.research_scheduler import (
    build_research_scheduler_report,
)


ROOT = Path(__file__).resolve().parents[4]


def run_research_cycle(
    *,
    execute: bool = False,
    max_jobs: int = 100,
    timeout_seconds: int = 1800,
    continue_on_failure: bool = False,
    resume: bool = False,
    restart: bool = False,
    self_heal: bool = True,
    max_recovery_attempts: int = 2,
    use_build_cache: bool = True,
    allowed_job_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Run or preview one dependency-aware research cycle.

    ``resume`` reuses the last incomplete execution checkpoint and skips
    successfully completed jobs.

    ``restart`` ignores the previous checkpoint and creates a fresh run.
    """
    if resume and restart:
        raise ValueError(
            "resume and restart are mutually exclusive"
        )

    invocation_started_at = datetime.now(UTC)

    initial_scheduler = (
        build_research_scheduler_report()
    )

    state_hash = str(
        initial_scheduler["state_hash"]
    )

    prior_state: dict[str, Any] = {}
    resumed = False
    restarted = bool(restart)

    if resume:
        prior_state = load_resume_state()

        if not is_resumable_state(
            prior_state
        ):
            raise ValueError(
                "No resumable research cycle exists."
            )

        resumed = True

    if resumed:
        run_id = str(
            prior_state["run_id"]
        )
        logical_started_at = str(
            prior_state.get(
                "started_at",
                invocation_started_at.isoformat(),
            )
        )
        results: list[dict[str, Any]] = [
            dict(result)
            for result in prior_state.get(
                "results",
                [],
            )
            if isinstance(result, dict)
        ]
        completed_jobs = completed_job_ids(
            prior_state
        )
    else:
        run_id = build_run_id(
            state_hash=state_hash,
            started_at=invocation_started_at,
            execute=execute,
        )
        logical_started_at = (
            invocation_started_at.isoformat()
        )
        results = []
        completed_jobs: set[str] = set()

    current_schedule = _read_schedule(
        initial_scheduler
    )

    initial_plan = build_execution_plan(
        current_schedule,
        execute=execute,
        max_jobs=max_jobs,
    )

    if completed_jobs:
        initial_plan = initial_plan[
            ~initial_plan[
                "job_id"
            ].astype(str).isin(
                completed_jobs
            )
        ].reset_index(drop=True)

    nonselected = (
        classify_nonselected_jobs(
            current_schedule
        )
    )

    attempted_this_invocation: set[str] = set()
    attempt_counts: dict[str, int] = {}
    invocation_attempt_count = 0
    recovery_attempt_count = 0
    healed_job_ids: set[str] = set()
    recovery_failed_job_ids: set[str] = set()
    cached_job_ids: set[str] = set()
    cache_miss_reasons: dict[str, str] = {}
    scheduler_stalled = False
    stall_reason = ""
    previous_schedule_signature = (
        schedule_signature(
            current_schedule
        )
    )
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
        write_resume_state(
            run_id=run_id,
            status="RUNNING",
            execute=True,
            started_at=logical_started_at,
            initial_state_hash=state_hash,
            results=results,
            resumed=resumed,
            restarted=restarted,
        )

        try:
            while (
                invocation_attempt_count
                < max(0, int(max_jobs))
            ):
                scheduler_report = (
                    build_research_scheduler_report()
                )

                current_schedule = _read_schedule(
                    scheduler_report
                )

                current_signature = (
                    schedule_signature(
                        current_schedule
                    )
                )

                plan = build_execution_plan(
                    current_schedule,
                    execute=True,
                    max_jobs=max_jobs,
                )

                available_rows = []

                for _, candidate in plan.iterrows():
                    candidate_id = str(
                        candidate["job_id"]
                    )

                    if candidate_id in completed_jobs:
                        continue

                    if (
                        allowed_job_ids is not None
                        and candidate_id
                        not in allowed_job_ids
                    ):
                        continue

                    attempts = attempt_counts.get(
                        candidate_id,
                        0,
                    )

                    allowed_attempts = (
                        max(
                            1,
                            int(
                                max_recovery_attempts
                            ),
                        )
                        if self_heal
                        else 1
                    )

                    if attempts >= allowed_attempts:
                        continue

                    available_rows.append(
                        candidate
                    )

                if not available_rows:
                    blocked = blocked_job_ids(
                        current_schedule
                    )

                    if blocked:
                        scheduler_stalled = True
                        stall_reason = (
                            "No executable recovery root "
                            "remained while blocked jobs "
                            "were still present."
                        )

                    break

                candidate = available_rows[0]

                next_job_id = str(
                    candidate["job_id"]
                )

                attempted_this_invocation.add(
                    next_job_id
                )

                attempt_counts[next_job_id] = (
                    attempt_counts.get(
                        next_job_id,
                        0,
                    )
                    + 1
                )

                attempt_number = (
                    attempt_counts[
                        next_job_id
                    ]
                )

                invocation_attempt_count += 1

                if attempt_number > 1:
                    recovery_attempt_count += 1

                cache_decision = {
                    "cache_hit": False,
                    "reason": (
                        "BUILD_CACHE_DISABLED"
                    ),
                }

                if use_build_cache:
                    cache_decision = (
                        evaluate_build_cache(
                            next_job_id
                        )
                    )

                if bool(
                    cache_decision.get(
                        "cache_hit",
                        False,
                    )
                ):
                    cached_job_ids.add(
                        next_job_id
                    )
                    completed_jobs.add(
                        next_job_id
                    )

                    cached_result = {
                        "job_id": next_job_id,
                        "status": "CACHED",
                        "started_at": "",
                        "completed_at": "",
                        "duration_seconds": 0.0,
                        "returncode": 0,
                        "stdout_path": "",
                        "stderr_path": "",
                        "error": "",
                        "execution_authorized": True,
                        "execution_instruction": False,
                        "build_cache_enabled": True,
                        "cache_hit": True,
                        "cache_reason": (
                            cache_decision.get(
                                "reason",
                                "CACHE_HIT",
                            )
                        ),
                        "cached_run_id": (
                            cache_decision.get(
                                "cached_run_id",
                                "",
                            )
                        ),
                        "artifact_verified": True,
                        "artifact_healed": True,
                        "scheduler_healthy": True,
                        "contract_healthy": True,
                        "retry_pending": False,
                    }

                    results.append(
                        cached_result
                    )

                    record_execution_provenance(
                        job_id=next_job_id,
                        run_id=run_id,
                        result=cached_result,
                        attempt=attempt_number,
                        cache_decision=(
                            cache_decision
                        ),
                        verification={
                            "verified": True,
                            "healed": True,
                            "scheduler_healthy": True,
                            "contract_healthy": True,
                            "status": "CURRENT",
                        },
                    )

                    write_resume_state(
                        run_id=run_id,
                        status="RUNNING",
                        execute=True,
                        started_at=(
                            logical_started_at
                        ),
                        initial_state_hash=(
                            state_hash
                        ),
                        results=results,
                        failure_detected=(
                            failure_detected
                        ),
                        resumed=resumed,
                        restarted=restarted,
                    )

                    continue

                cache_miss_reasons[
                    next_job_id
                ] = str(
                    cache_decision.get(
                        "reason",
                        "CACHE_MISS",
                    )
                )

                raw_result = execute_job(
                    job_id=next_job_id,
                    run_id=run_id,
                    timeout_seconds=(
                        timeout_seconds
                    ),
                    root=ROOT,
                )

                raw_result = dict(
                    raw_result
                )

                refreshed_report = (
                    build_research_scheduler_report()
                )

                refreshed_schedule = (
                    _read_schedule(
                        refreshed_report
                    )
                )

                verification = verify_job_health(
                    refreshed_schedule,
                    next_job_id,
                )

                command_succeeded = (
                    str(
                        raw_result.get(
                            "status",
                            "",
                        )
                    )
                    == "SUCCEEDED"
                )

                healed = bool(
                    command_succeeded
                    and (
                        not self_heal
                        or verification.get(
                            "healed",
                            False,
                        )
                    )
                )

                retry_allowed = can_retry(
                    attempts=attempt_number,
                    max_recovery_attempts=(
                        max_recovery_attempts
                    ),
                    self_heal=self_heal,
                )

                retry_pending = bool(
                    not healed
                    and retry_allowed
                )

                if healed:
                    raw_result["status"] = (
                        "SUCCEEDED"
                    )
                    completed_jobs.add(
                        next_job_id
                    )
                    healed_job_ids.add(
                        next_job_id
                    )

                    if use_build_cache:
                        record_successful_build(
                            next_job_id,
                            run_id=run_id,
                        )
                elif retry_pending:
                    raw_result["status"] = (
                        "RETRY_PENDING"
                    )
                else:
                    raw_result["status"] = (
                        "RECOVERY_FAILED"
                    )
                    recovery_failed_job_ids.add(
                        next_job_id
                    )
                    failure_detected = True

                result = annotate_recovery_result(
                    raw_result,
                    attempt=attempt_number,
                    verification=verification,
                    retry_pending=retry_pending,
                    self_heal=self_heal,
                )

                results.append(result)

                record_execution_provenance(
                    job_id=next_job_id,
                    run_id=run_id,
                    result=result,
                    attempt=attempt_number,
                    cache_decision=(
                        cache_decision
                    ),
                    verification=verification,
                )

                refreshed_signature = (
                    schedule_signature(
                        refreshed_schedule
                    )
                )

                if (
                    retry_pending
                    and refreshed_signature
                    == current_signature
                    and attempt_number
                    >= max(
                        1,
                        int(
                            max_recovery_attempts
                        ),
                    )
                ):
                    scheduler_stalled = True
                    stall_reason = (
                        "Recovery attempts produced no "
                        "scheduler-state progress."
                    )

                previous_schedule_signature = (
                    refreshed_signature
                )

                write_resume_state(
                    run_id=run_id,
                    status=(
                        "FAILED"
                        if failure_detected
                        else "RUNNING"
                    ),
                    execute=True,
                    started_at=logical_started_at,
                    initial_state_hash=state_hash,
                    results=results,
                    failure_detected=(
                        failure_detected
                    ),
                    resumed=resumed,
                    restarted=restarted,
                )

                if (
                    failure_detected
                    and not continue_on_failure
                ):
                    break

                if scheduler_stalled:
                    failure_detected = True
                    break

        except BaseException:
            write_resume_state(
                run_id=run_id,
                status="INTERRUPTED",
                execute=True,
                started_at=logical_started_at,
                initial_state_hash=state_hash,
                results=results,
                failure_detected=True,
                resumed=resumed,
                restarted=restarted,
            )
            raise

        final_scheduler = (
            build_research_scheduler_report()
        )

        current_schedule = _read_schedule(
            final_scheduler
        )

        nonselected = (
            classify_nonselected_jobs(
                current_schedule
            )
        )

    completed_at = datetime.now(UTC)

    if execute:
        write_resume_state(
            run_id=run_id,
            status=(
                "FAILED"
                if failure_detected
                else "SUCCEEDED"
            ),
            execute=True,
            started_at=logical_started_at,
            completed_at=(
                completed_at.isoformat()
            ),
            initial_state_hash=state_hash,
            results=results,
            failure_detected=(
                failure_detected
            ),
            resumed=resumed,
            restarted=restarted,
        )

    results_frame = pd.DataFrame(
        results
    )

    return {
        "run_id": run_id,
        "execute": execute,
        "resumed": resumed,
        "restarted": restarted,
        "resumed_from_run_id": (
            run_id
            if resumed
            else ""
        ),
        "completed_job_ids": sorted(
            completed_jobs
        ),
        "attempted_this_invocation": sorted(
            attempted_this_invocation
        ),
        "attempt_counts": dict(
            sorted(
                attempt_counts.items()
            )
        ),
        "execution_attempt_count": int(
            invocation_attempt_count
        ),
        "recovery_attempt_count": int(
            recovery_attempt_count
        ),
        "healed_job_ids": sorted(
            healed_job_ids
        ),
        "recovery_failed_job_ids": sorted(
            recovery_failed_job_ids
        ),
        "cached_job_ids": sorted(
            cached_job_ids
        ),
        "cache_miss_reasons": dict(
            sorted(
                cache_miss_reasons.items()
            )
        ),
        "build_cache_enabled": bool(
            use_build_cache
        ),
        "execution_scope_restricted": bool(
            allowed_job_ids is not None
        ),
        "allowed_job_ids": sorted(
            allowed_job_ids
            or set()
        ),
        "self_healing_enabled": bool(
            self_heal
        ),
        "max_recovery_attempts": int(
            max_recovery_attempts
        ),
        "scheduler_stalled": bool(
            scheduler_stalled
        ),
        "stall_reason": str(
            stall_reason
        ),
        "started_at": logical_started_at,
        "invocation_started_at": (
            invocation_started_at.isoformat()
        ),
        "completed_at": (
            completed_at.isoformat()
        ),
        "duration_seconds": round(
            (
                completed_at
                - invocation_started_at
            ).total_seconds(),
            8,
        ),
        "initial_scheduler": (
            initial_scheduler
        ),
        "initial_plan": initial_plan,
        "results": results_frame,
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


def _read_schedule(
    scheduler_report: dict[str, Any],
) -> pd.DataFrame:
    """Read the schedule produced by one scheduler refresh."""
    return pd.read_csv(
        scheduler_report[
            "outputs"
        ][
            "research_schedule_csv"
        ]
    )


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
