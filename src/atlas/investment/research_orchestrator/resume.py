"""Persistent resume state for dependency-aware research cycles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from atlas.investment.research_orchestrator.config import (
    EXECUTION_STATE_JSON,
)


RESUMABLE_STATUSES = {
    "RUNNING",
    "FAILED",
    "INTERRUPTED",
}


def load_resume_state(
    path: Path = EXECUTION_STATE_JSON,
) -> dict[str, Any]:
    """Load a prior checkpoint.

    Missing, empty, malformed, or non-object files are treated as absent state.
    """
    if not path.exists() or path.stat().st_size == 0:
        return {}

    try:
        payload = json.loads(
            path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return {}

    return payload if isinstance(payload, dict) else {}


def completed_job_ids(
    state: dict[str, Any],
) -> set[str]:
    """Return successfully completed job IDs from a checkpoint."""
    completed = {
        str(job_id)
        for job_id in state.get(
            "completed_job_ids",
            [],
        )
        if str(job_id)
    }

    for result in state.get("results", []) or []:
        if not isinstance(result, dict):
            continue

        if str(result.get("status", "")) != "SUCCEEDED":
            continue

        job_id = str(result.get("job_id", ""))

        if job_id:
            completed.add(job_id)

    return completed


def is_resumable_state(
    state: dict[str, Any],
) -> bool:
    """Return whether a checkpoint represents an incomplete execution."""
    return bool(
        state
        and state.get("run_id")
        and str(state.get("status", ""))
        in RESUMABLE_STATUSES
        and bool(
            state.get(
                "execute",
                state.get("mode") == "EXECUTE",
            )
        )
    )


def write_resume_state(
    *,
    run_id: str,
    status: str,
    execute: bool,
    started_at: str,
    initial_state_hash: str,
    results: Iterable[dict[str, Any]],
    path: Path = EXECUTION_STATE_JSON,
    completed_at: str = "",
    failure_detected: bool = False,
    resumed: bool = False,
    restarted: bool = False,
) -> dict[str, Any]:
    """Persist an atomic execution checkpoint."""
    normalized_results = [
        dict(result)
        for result in results
    ]

    completed = sorted({
        str(result.get("job_id", ""))
        for result in normalized_results
        if str(result.get("status", ""))
        == "SUCCEEDED"
        and str(result.get("job_id", ""))
    })

    state = {
        "run_id": str(run_id),
        "status": str(status),
        "execute": bool(execute),
        "mode": (
            "EXECUTE"
            if execute
            else "DRY_RUN"
        ),
        "started_at": str(started_at),
        "completed_at": str(completed_at),
        "initial_state_hash": str(
            initial_state_hash
        ),
        "failure_detected": bool(
            failure_detected
        ),
        "resumed": bool(resumed),
        "restarted": bool(restarted),
        "resumable": bool(
            execute
            and str(status)
            in RESUMABLE_STATUSES
        ),
        "completed_job_ids": completed,
        "results": normalized_results,
    }

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            state,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)

    return state


__all__ = [
    "RESUMABLE_STATUSES",
    "completed_job_ids",
    "is_resumable_state",
    "load_resume_state",
    "write_resume_state",
]
