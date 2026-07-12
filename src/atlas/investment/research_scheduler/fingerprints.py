"""Persistent artifact fingerprints for incremental Atlas builds.

The canonical job registry remains the only owner of job outputs and dependency
edges. This module adds content identity and persistent dependency snapshots.

A job is content-stale when the current content hash of one or more dependency
outputs differs from the dependency hashes acknowledged by the job's last known
output build.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from atlas.investment.research_scheduler.config import (
    FINGERPRINT_STATE_JSON,
)
from atlas.investment.research_scheduler.registry import (
    JOBS,
    ResearchJobSpec,
)


FINGERPRINT_SCHEMA_VERSION = "1.0.0"
HASH_ALGORITHM = "sha256"
CHUNK_SIZE = 1024 * 1024


def hash_file(
    path: Path,
) -> str:
    """Return a deterministic SHA-256 hash for one file."""
    if not path.exists() or not path.is_file():
        return ""

    digest = hashlib.sha256()

    try:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(CHUNK_SIZE)

                if not chunk:
                    break

                digest.update(chunk)
    except OSError:
        return ""

    return digest.hexdigest()


def load_fingerprint_state(
    path: Path = FINGERPRINT_STATE_JSON,
) -> dict[str, Any]:
    """Load persistent fingerprint state safely."""
    if not path.exists() or path.stat().st_size == 0:
        return {}

    try:
        payload = json.loads(
            path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(payload, dict):
        return {}

    jobs = payload.get("jobs", {})

    if not isinstance(jobs, dict):
        payload["jobs"] = {}

    return payload


def write_fingerprint_state(
    state: Mapping[str, Any],
    path: Path = FINGERPRINT_STATE_JSON,
) -> None:
    """Persist fingerprint state atomically."""
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
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)


def apply_content_fingerprints(
    freshness_rows: Iterable[Mapping[str, Any]],
    *,
    jobs: Sequence[ResearchJobSpec] = JOBS,
    state: Mapping[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Enrich rows with content hashes and produce the next persisted state.

    Rules:

    1. On first observation, capture a baseline without creating content dirtiness.
    2. Compare each job's current dependency hashes with its acknowledged snapshot.
    3. If dependency hashes differ and the job output has not changed, mark the job
       content-stale.
    4. If the job output hash changed, treat it as a rebuild and acknowledge the
       current dependency hashes.
    5. Do not acknowledge changed dependency hashes while the old downstream output
       remains in place.
    """
    rows = [
        dict(row)
        for row in freshness_rows
    ]

    row_map = {
        str(row.get("job_id", "")): row
        for row in rows
        if str(row.get("job_id", ""))
    }

    previous_state = (
        dict(state)
        if state is not None
        else load_fingerprint_state()
    )

    previous_jobs = previous_state.get(
        "jobs",
        {},
    )

    if not isinstance(previous_jobs, dict):
        previous_jobs = {}

    job_map = {
        job.job_id: job
        for job in jobs
    }

    current_output_hashes: dict[str, str] = {}

    for job in jobs:
        row = row_map.get(job.job_id)

        if row is None:
            continue

        output_hash = ""

        if bool(row.get("exists", False)):
            output_hash = hash_file(
                job.output_path
            )

        current_output_hashes[
            job.job_id
        ] = output_hash

        row["content_hash"] = output_hash
        row["hash_algorithm"] = HASH_ALGORITHM
        row["fingerprint_available"] = bool(
            output_hash
        )

    next_jobs: dict[str, dict[str, Any]] = {}

    for job in jobs:
        row = row_map.get(job.job_id)

        if row is None:
            continue

        output_hash = current_output_hashes.get(
            job.job_id,
            "",
        )

        current_dependency_hashes = {
            dependency_id: current_output_hashes.get(
                dependency_id,
                "",
            )
            for dependency_id in job.dependencies
        }

        previous = previous_jobs.get(
            job.job_id,
            {},
        )

        if not isinstance(previous, dict):
            previous = {}

        previous_output_hash = str(
            previous.get(
                "output_hash",
                "",
            )
        )

        previous_dependency_hashes = previous.get(
            "dependency_hashes",
            {},
        )

        if not isinstance(
            previous_dependency_hashes,
            dict,
        ):
            previous_dependency_hashes = {}

        has_baseline = bool(previous)

        output_content_changed = bool(
            has_baseline
            and output_hash
            and previous_output_hash
            and output_hash
            != previous_output_hash
        )

        changed_dependencies = [
            dependency_id
            for dependency_id
            in job.dependencies
            if (
                dependency_id
                in previous_dependency_hashes
                and str(
                    current_dependency_hashes.get(
                        dependency_id,
                        "",
                    )
                )
                != str(
                    previous_dependency_hashes.get(
                        dependency_id,
                        "",
                    )
                )
            )
        ]

        missing_dependency_baseline = [
            dependency_id
            for dependency_id
            in job.dependencies
            if dependency_id
            not in previous_dependency_hashes
        ]

        fingerprint_baseline_complete = bool(
            has_baseline
            and not missing_dependency_baseline
        )

        content_stale = bool(
            fingerprint_baseline_complete
            and changed_dependencies
            and not output_content_changed
        )

        row["previous_content_hash"] = (
            previous_output_hash
        )
        row["output_content_changed"] = (
            output_content_changed
        )
        row["content_stale"] = content_stale
        row["content_changed_dependencies"] = (
            "|".join(changed_dependencies)
        )
        row["fingerprint_baseline_complete"] = (
            fingerprint_baseline_complete
        )
        row["fingerprint_baseline_missing"] = (
            "|".join(
                missing_dependency_baseline
            )
        )

        # A new output hash means the producing job ran. Its current dependency
        # hashes can now be acknowledged. Clean jobs and first-run baselines are
        # also safe to persist.
        acknowledge_dependencies = bool(
            not has_baseline
            or output_content_changed
            or not content_stale
        )

        if acknowledge_dependencies:
            acknowledged_dependency_hashes = (
                current_dependency_hashes
            )
        else:
            acknowledged_dependency_hashes = {
                str(key): str(value)
                for key, value
                in previous_dependency_hashes.items()
            }

        next_jobs[job.job_id] = {
            "output_path": str(
                job.output_path
            ),
            "output_hash": output_hash,
            "dependency_hashes": (
                acknowledged_dependency_hashes
            ),
        }

    for row in rows:
        apply_fingerprint_defaults(row)

    next_state = {
        "schema_version": (
            FINGERPRINT_SCHEMA_VERSION
        ),
        "hash_algorithm": HASH_ALGORITHM,
        "jobs": next_jobs,
    }

    return rows, next_state


def apply_fingerprint_defaults(
    row: dict[str, Any],
) -> None:
    """Ensure every row exposes the complete fingerprint contract."""
    defaults = {
        "content_hash": "",
        "previous_content_hash": "",
        "hash_algorithm": HASH_ALGORITHM,
        "fingerprint_available": False,
        "fingerprint_baseline_complete": False,
        "fingerprint_baseline_missing": "",
        "output_content_changed": False,
        "content_stale": False,
        "content_changed_dependencies": "",
    }

    for key, value in defaults.items():
        row.setdefault(key, value)


__all__ = [
    "FINGERPRINT_SCHEMA_VERSION",
    "HASH_ALGORITHM",
    "apply_content_fingerprints",
    "apply_fingerprint_defaults",
    "hash_file",
    "load_fingerprint_state",
    "write_fingerprint_state",
]
