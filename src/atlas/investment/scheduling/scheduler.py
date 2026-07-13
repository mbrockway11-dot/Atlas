"""Restart-safe deterministic scheduler for Atlas shadow workflows."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from atlas.investment.scheduling.jobs import (
    DEFAULT_JOBS,
    ScheduledJob,
    validate_job_graph,
)
from atlas.investment.scheduling.sessions import (
    evaluate_market_session,
)


OUTPUT_DIR = Path(
    "output/investment_scheduler"
)

SCHEDULER_STATE_JSON = (
    OUTPUT_DIR
    / "scheduler_state.json"
)

SCHEDULER_DECISION_JSON = (
    OUTPUT_DIR
    / "scheduler_decision.json"
)

SCHEDULER_HISTORY_JSONL = (
    OUTPUT_DIR
    / "scheduler_history.jsonl"
)

SCHEDULER_VERSION = "1.0.0"


def evaluate_scheduler(
    *,
    jobs: Iterable[
        ScheduledJob
    ] = DEFAULT_JOBS,
    state: Mapping[
        str,
        Any,
    ] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Evaluate due jobs without executing their command plans."""
    current = ensure_utc(
        now
        or datetime.now(
            UTC
        )
    )

    rows = tuple(
        jobs
    )

    graph = validate_job_graph(
        rows
    )

    if not graph["valid"]:
        raise ValueError(
            "SCHEDULER_JOB_GRAPH_INVALID:"
            + "|".join(
                graph["errors"]
            )
        )

    scheduler_state = dict(
        state or {}
    )

    job_state = dict(
        scheduler_state.get(
            "jobs",
            {},
        )
        or {}
    )

    decisions: list[
        dict[str, Any]
    ] = []

    selected_names: set[str] = set()

    for job in rows:
        session = (
            evaluate_market_session(
                job.session_name,
                now=current,
            )
        )

        prior = dict(
            job_state.get(
                job.name,
                {},
            )
            or {}
        )

        last_completed_at = str(
            prior.get(
                "last_completed_at",
                "",
            )
        )

        cadence_due = is_cadence_due(
            last_completed_at=(
                last_completed_at
            ),
            cadence_seconds=(
                job.cadence_seconds
            ),
            now=current,
        )

        dependencies_satisfied = all(
            dependency
            in selected_names
            or dependency_has_success(
                dependency,
                job_state,
            )
            for dependency
            in job.dependencies
        )

        reasons: list[str] = []

        if not job.enabled:
            reasons.append(
                "JOB_DISABLED"
            )

        if not session.is_open:
            reasons.append(
                "SESSION_CLOSED:"
                + session.reason
            )

        if not cadence_due:
            reasons.append(
                "CADENCE_NOT_DUE"
            )

        if not dependencies_satisfied:
            reasons.append(
                "DEPENDENCIES_NOT_SATISFIED"
            )

        due = bool(
            job.enabled
            and session.is_open
            and cadence_due
            and dependencies_satisfied
        )

        if due:
            selected_names.add(
                job.name
            )

        decisions.append({
            "job": job.to_dict(),
            "due": due,
            "reasons": reasons,
            "session": (
                session.to_dict()
            ),
            "last_completed_at": (
                last_completed_at
            ),
            "prior_status": str(
                prior.get(
                    "last_status",
                    "",
                )
            ),
        })

    decision_id = build_decision_id(
        current,
        decisions,
    )

    due_jobs = [
        row["job"]["name"]
        for row in decisions
        if row["due"]
    ]

    execution_plan = [
        {
            "name": (
                row["job"]["name"]
            ),
            "command": (
                row["job"]["command"]
            ),
            "paper_only": (
                row["job"][
                    "paper_only"
                ]
            ),
            "session_name": (
                row["job"][
                    "session_name"
                ]
            ),
        }
        for row in decisions
        if row["due"]
    ]

    return {
        "success": True,
        "version": (
            SCHEDULER_VERSION
        ),
        "decision_id": (
            decision_id
        ),
        "evaluated_at": (
            current.isoformat()
        ),
        "due_jobs": due_jobs,
        "execution_plan": (
            execution_plan
        ),
        "decisions": decisions,
        "graph_validation": (
            graph
        ),
        "contract": {
            "decision_only": True,
            "commands_not_executed": True,
            "paper_only": True,
            "submits_orders": False,
            "mutates_account": False,
            "credentials_used": False,
            "live_execution": False,
        },
    }


def apply_job_results(
    *,
    state: Mapping[
        str,
        Any,
    ] | None,
    decision: Mapping[
        str,
        Any,
    ],
    results: Mapping[
        str,
        Mapping[
            str,
            Any,
        ],
    ],
) -> dict[str, Any]:
    """Apply externally produced job results to scheduler state."""
    current_state = dict(
        state or {}
    )

    jobs = dict(
        current_state.get(
            "jobs",
            {},
        )
        or {}
    )

    evaluated_at = str(
        decision.get(
            "evaluated_at",
            "",
        )
    )

    due_jobs = {
        str(value)
        .strip()
        .upper()
        for value
        in decision.get(
            "due_jobs",
            [],
        )
    }

    for raw_name, result in (
        results.items()
    ):
        name = str(
            raw_name
        ).strip().upper()

        if name not in due_jobs:
            raise ValueError(
                "JOB_RESULT_NOT_IN_DECISION:"
                + name
            )

        previous = dict(
            jobs.get(
                name,
                {},
            )
            or {}
        )

        success = bool(
            result.get(
                "success",
                False,
            )
        )

        attempt_count = (
            int(
                previous.get(
                    "attempt_count",
                    0,
                )
            )
            + 1
        )

        previous.update({
            "attempt_count": (
                attempt_count
            ),
            "last_attempted_at": (
                evaluated_at
            ),
            "last_status": (
                "SUCCESS"
                if success
                else "FAILED"
            ),
            "last_error": str(
                result.get(
                    "error",
                    "",
                )
            ),
            "last_result_id": str(
                result.get(
                    "result_id",
                    "",
                )
            ),
            "last_decision_id": str(
                decision.get(
                    "decision_id",
                    "",
                )
            ),
        })

        if success:
            previous[
                "last_completed_at"
            ] = evaluated_at

        jobs[name] = previous

    return {
        "version": (
            SCHEDULER_VERSION
        ),
        "updated_at": (
            evaluated_at
        ),
        "last_decision_id": str(
            decision.get(
                "decision_id",
                "",
            )
        ),
        "jobs": jobs,
        "contract": {
            "paper_only": True,
            "live_execution": False,
        },
    }


def load_scheduler_state(
    path: Path = (
        SCHEDULER_STATE_JSON
    ),
) -> dict[str, Any]:
    """Load the persistent scheduler checkpoint."""
    if not path.exists():
        return {
            "version": (
                SCHEDULER_VERSION
            ),
            "jobs": {},
        }

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(
            "SCHEDULER_STATE_INVALID"
        )

    jobs = payload.get(
        "jobs",
        {},
    )

    if not isinstance(
        jobs,
        dict,
    ):
        raise ValueError(
            "SCHEDULER_JOBS_STATE_INVALID"
        )

    return payload


def write_scheduler_outputs(
    *,
    decision: Mapping[
        str,
        Any,
    ],
    state: Mapping[
        str,
        Any,
    ] | None = None,
    decision_path: Path = (
        SCHEDULER_DECISION_JSON
    ),
    state_path: Path = (
        SCHEDULER_STATE_JSON
    ),
    history_path: Path = (
        SCHEDULER_HISTORY_JSONL
    ),
) -> None:
    """Persist the latest decision, optional state, and history row."""
    write_json_atomic(
        decision_path,
        decision,
    )

    if state is not None:
        write_json_atomic(
            state_path,
            state,
        )

    history_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with history_path.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(
            json.dumps(
                {
                    "decision_id": (
                        decision.get(
                            "decision_id",
                            "",
                        )
                    ),
                    "evaluated_at": (
                        decision.get(
                            "evaluated_at",
                            "",
                        )
                    ),
                    "due_jobs": (
                        decision.get(
                            "due_jobs",
                            [],
                        )
                    ),
                    "success": bool(
                        decision.get(
                            "success",
                            False,
                        )
                    ),
                },
                sort_keys=True,
                default=str,
            )
            + "\n"
        )


def is_cadence_due(
    *,
    last_completed_at: str,
    cadence_seconds: int,
    now: datetime,
) -> bool:
    """Return whether one job has exceeded its required cadence."""
    if not last_completed_at:
        return True

    previous = parse_time(
        last_completed_at
    )

    elapsed_seconds = (
        now
        - previous
    ).total_seconds()

    return elapsed_seconds >= int(
        cadence_seconds
    )


def dependency_has_success(
    dependency: str,
    job_state: Mapping[
        str,
        Any,
    ],
) -> bool:
    """Return whether a prior dependency has a persisted success."""
    value = dict(
        job_state.get(
            dependency,
            {},
        )
        or {}
    )

    return bool(
        value.get(
            "last_status"
        )
        == "SUCCESS"
        and value.get(
            "last_completed_at"
        )
    )


def build_decision_id(
    now: datetime,
    decisions,
) -> str:
    """Build a deterministic scheduler-decision identifier."""
    payload = {
        "evaluated_at": (
            now.isoformat()
        ),
        "decisions": [
            {
                "name": (
                    row["job"]["name"]
                ),
                "due": row["due"],
                "reasons": (
                    row["reasons"]
                ),
            }
            for row in decisions
        ],
    }

    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return (
        "SCHEDULER-DECISION-"
        + digest[:24]
    )


def parse_time(
    value: str,
) -> datetime:
    """Parse an ISO timestamp and normalize it to UTC."""
    text = str(
        value
    ).strip()

    if not text:
        raise ValueError(
            "SCHEDULER_TIMESTAMP_REQUIRED"
        )

    if text.endswith("Z"):
        text = (
            text[:-1]
            + "+00:00"
        )

    parsed = datetime.fromisoformat(
        text
    )

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=UTC
        )

    return parsed.astimezone(
        UTC
    )


def ensure_utc(
    value: datetime,
) -> datetime:
    """Normalize a datetime to UTC."""
    if value.tzinfo is None:
        value = value.replace(
            tzinfo=UTC
        )

    return value.astimezone(
        UTC
    )


def write_json_atomic(
    path: Path,
    payload: Mapping[
        str,
        Any,
    ],
) -> None:
    """Write one JSON object using atomic replacement."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix
        + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            dict(payload),
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


__all__ = [
    "SCHEDULER_DECISION_JSON",
    "SCHEDULER_HISTORY_JSONL",
    "SCHEDULER_STATE_JSON",
    "SCHEDULER_VERSION",
    "apply_job_results",
    "evaluate_scheduler",
    "load_scheduler_state",
    "write_scheduler_outputs",
]
