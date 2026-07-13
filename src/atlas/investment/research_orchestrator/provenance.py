"""Immutable execution provenance for Atlas research jobs.

Each executed or cached job produces one append-only provenance event containing
the exact command/configuration identity, required input hashes, required output
hashes, cache decision, recovery state, and producing run.

The JSONL ledger is authoritative history. The latest-state JSON is a derived
index for fast lookup and may be rebuilt from the ledger.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from atlas.investment.artifact_contracts import (
    contract_for_job,
)
from atlas.investment.artifact_lineage import (
    input_contract_for_job,
)
from atlas.investment.research_orchestrator.build_cache import (
    build_identity_hash,
    job_command_signature,
    required_input_manifest,
    required_output_manifest,
)
from atlas.investment.research_orchestrator.config import (
    PROVENANCE_JSONL,
    PROVENANCE_LATEST_JSON,
)


PROVENANCE_SCHEMA_VERSION = "1.0.0"


def build_provenance_event(
    *,
    job_id: str,
    run_id: str,
    result: Mapping[str, Any],
    attempt: int = 1,
    cache_decision: Mapping[str, Any] | None = None,
    verification: Mapping[str, Any] | None = None,
    recorded_at: str | None = None,
) -> dict[str, Any]:
    """Build one deterministic, self-contained provenance event."""
    cache = dict(
        cache_decision or {}
    )
    verified = dict(
        verification or {}
    )

    timestamp = (
        recorded_at
        or datetime.now(UTC).isoformat()
    )

    command_signature = (
        job_command_signature(
            job_id
        )
    )

    inputs = required_input_manifest(
        job_id
    )
    outputs = required_output_manifest(
        job_id
    )

    input_contract = (
        input_contract_for_job(
            job_id
        )
    )
    output_contract = (
        contract_for_job(
            job_id
        )
    )

    event_payload = {
        "schema_version": (
            PROVENANCE_SCHEMA_VERSION
        ),
        "recorded_at": timestamp,
        "run_id": str(run_id),
        "job_id": str(job_id),
        "status": str(
            result.get(
                "status",
                "UNKNOWN",
            )
        ),
        "attempt": int(attempt),
        "returncode": result.get(
            "returncode"
        ),
        "started_at": str(
            result.get(
                "started_at",
                "",
            )
        ),
        "completed_at": str(
            result.get(
                "completed_at",
                "",
            )
        ),
        "duration_seconds": float(
            result.get(
                "duration_seconds",
                0.0,
            )
            or 0.0
        ),
        "stdout_path": str(
            result.get(
                "stdout_path",
                "",
            )
        ),
        "stderr_path": str(
            result.get(
                "stderr_path",
                "",
            )
        ),
        "error": str(
            result.get(
                "error",
                "",
            )
        ),
        "command_signature": (
            command_signature
        ),
        "build_identity_hash": (
            build_identity_hash(
                job_id
            )
        ),
        "required_input_manifest": (
            inputs
        ),
        "required_output_manifest": (
            outputs
        ),
        "input_contract": {
            "required_paths": [
                str(path)
                for path
                in input_contract.required_paths
            ],
            "optional_paths": [
                str(path)
                for path
                in input_contract.optional_paths
            ],
        },
        "output_contract": {
            "required_paths": [
                str(path)
                for path
                in output_contract.required_paths
            ],
            "optional_paths": [
                str(path)
                for path
                in output_contract.optional_paths
            ],
        },
        "cache": {
            "enabled": bool(
                result.get(
                    "build_cache_enabled",
                    bool(cache),
                )
            ),
            "hit": bool(
                result.get(
                    "cache_hit",
                    cache.get(
                        "cache_hit",
                        False,
                    ),
                )
            ),
            "reason": str(
                result.get(
                    "cache_reason",
                    cache.get(
                        "reason",
                        "",
                    ),
                )
            ),
            "cached_run_id": str(
                result.get(
                    "cached_run_id",
                    cache.get(
                        "cached_run_id",
                        "",
                    ),
                )
            ),
        },
        "verification": {
            "verified": bool(
                result.get(
                    "artifact_verified",
                    verified.get(
                        "verified",
                        False,
                    ),
                )
            ),
            "healed": bool(
                result.get(
                    "artifact_healed",
                    verified.get(
                        "healed",
                        False,
                    ),
                )
            ),
            "scheduler_healthy": bool(
                result.get(
                    "scheduler_healthy",
                    verified.get(
                        "scheduler_healthy",
                        False,
                    ),
                )
            ),
            "contract_healthy": bool(
                result.get(
                    "contract_healthy",
                    verified.get(
                        "contract_healthy",
                        False,
                    ),
                )
            ),
            "post_execution_status": str(
                result.get(
                    "post_execution_status",
                    verified.get(
                        "status",
                        "",
                    ),
                )
            ),
            "invalidation_reason": str(
                verified.get(
                    "invalidation_reason",
                    "",
                )
            ),
        },
        "recovery": {
            "attempt": int(
                result.get(
                    "recovery_attempt",
                    attempt,
                )
                or attempt
            ),
            "retry_pending": bool(
                result.get(
                    "retry_pending",
                    False,
                )
            ),
            "self_healing_enabled": bool(
                result.get(
                    "self_healing_enabled",
                    False,
                )
            ),
        },
    }

    event_payload["event_id"] = (
        provenance_event_id(
            event_payload
        )
    )

    return event_payload


def provenance_event_id(
    event: Mapping[str, Any],
) -> str:
    """Return a deterministic event ID excluding an existing event_id."""
    payload = {
        key: value
        for key, value in event.items()
        if key != "event_id"
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")

    return (
        "PROV-"
        + hashlib.sha256(
            encoded
        ).hexdigest()[:24]
    )


def append_provenance_event(
    event: Mapping[str, Any],
    *,
    ledger_path: Path = PROVENANCE_JSONL,
    latest_path: Path = PROVENANCE_LATEST_JSON,
) -> dict[str, Any]:
    """Append an event and update the derived latest-state index."""
    normalized = dict(event)

    ledger_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    latest_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with ledger_path.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(
            json.dumps(
                normalized,
                sort_keys=True,
                ensure_ascii=False,
                default=str,
            )
            + "\n"
        )

    latest = load_latest_provenance(
        latest_path
    )

    jobs = latest.get(
        "jobs",
        {},
    )

    if not isinstance(jobs, dict):
        jobs = {}

    jobs = dict(jobs)
    jobs[
        str(normalized["job_id"])
    ] = normalized

    status_counts = latest.get(
        "status_counts",
        {},
    )

    if not isinstance(
        status_counts,
        dict,
    ):
        status_counts = {}

    status = str(
        normalized.get(
            "status",
            "UNKNOWN",
        )
    )

    status_counts = dict(
        status_counts
    )
    status_counts[status] = int(
        status_counts.get(
            status,
            0,
        )
    ) + 1

    next_latest = {
        "schema_version": (
            PROVENANCE_SCHEMA_VERSION
        ),
        "updated_at": str(
            normalized.get(
                "recorded_at",
                "",
            )
        ),
        "event_count": int(
            latest.get(
                "event_count",
                0,
            )
        ) + 1,
        "status_counts": (
            status_counts
        ),
        "jobs": jobs,
    }

    write_latest_provenance(
        next_latest,
        latest_path,
    )

    return normalized


def record_execution_provenance(
    *,
    job_id: str,
    run_id: str,
    result: Mapping[str, Any],
    attempt: int = 1,
    cache_decision: Mapping[str, Any] | None = None,
    verification: Mapping[str, Any] | None = None,
    ledger_path: Path = PROVENANCE_JSONL,
    latest_path: Path = PROVENANCE_LATEST_JSON,
) -> dict[str, Any]:
    """Build and persist one execution provenance event."""
    event = build_provenance_event(
        job_id=job_id,
        run_id=run_id,
        result=result,
        attempt=attempt,
        cache_decision=cache_decision,
        verification=verification,
    )

    return append_provenance_event(
        event,
        ledger_path=ledger_path,
        latest_path=latest_path,
    )


def load_latest_provenance(
    path: Path = PROVENANCE_LATEST_JSON,
) -> dict[str, Any]:
    """Load the derived latest-state provenance index."""
    if not path.exists() or path.stat().st_size == 0:
        return empty_latest_state()

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return empty_latest_state()

    return (
        payload
        if isinstance(payload, dict)
        else empty_latest_state()
    )


def write_latest_provenance(
    state: Mapping[str, Any],
    path: Path = PROVENANCE_LATEST_JSON,
) -> None:
    """Write latest-state provenance atomically."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            dict(state),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)


def read_provenance_events(
    path: Path = PROVENANCE_JSONL,
) -> list[dict[str, Any]]:
    """Read valid provenance events from the append-only ledger."""
    if not path.exists():
        return []

    events: list[dict[str, Any]] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        for line in handle:
            text = line.strip()

            if not text:
                continue

            try:
                payload = json.loads(
                    text
                )
            except json.JSONDecodeError:
                continue

            if isinstance(payload, dict):
                events.append(payload)

    return events


def empty_latest_state() -> dict[str, Any]:
    return {
        "schema_version": (
            PROVENANCE_SCHEMA_VERSION
        ),
        "updated_at": "",
        "event_count": 0,
        "status_counts": {},
        "jobs": {},
    }


__all__ = [
    "PROVENANCE_SCHEMA_VERSION",
    "append_provenance_event",
    "build_provenance_event",
    "empty_latest_state",
    "load_latest_provenance",
    "provenance_event_id",
    "read_provenance_events",
    "record_execution_provenance",
    "write_latest_provenance",
]
