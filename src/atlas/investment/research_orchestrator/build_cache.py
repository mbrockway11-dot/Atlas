"""Deterministic build cache for Atlas research jobs.

The cache does not own execution order, dependencies, artifact paths, or
validation. It composes the canonical registries and contracts:

- research scheduler: job definitions and DAG dependencies;
- artifact lineage: required job inputs;
- artifact contracts: required job outputs;
- orchestrator safety: canonical executable commands;
- content fingerprints: SHA-256 file identity.

A cache hit means the prior successful build has the same command/configuration,
the same required input content, and the same validated required output content.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from atlas.investment.artifact_contracts import (
    contract_for_job,
    validate_job_outputs,
)
from atlas.investment.artifact_lineage import (
    input_contract_for_job,
    validate_job_inputs,
)
from atlas.investment.research_orchestrator.config import (
    BUILD_CACHE_JSON,
)
from atlas.investment.research_orchestrator.safety import (
    resolve_registered_command,
)
from atlas.investment.research_scheduler import (
    JOB_MAP,
)
from atlas.investment.research_scheduler.fingerprints import (
    HASH_ALGORITHM,
    hash_file,
)


BUILD_CACHE_SCHEMA_VERSION = "1.0.0"


def load_build_cache(
    path: Path = BUILD_CACHE_JSON,
) -> dict[str, Any]:
    """Load build-cache state safely."""
    if not path.exists() or path.stat().st_size == 0:
        return empty_cache_state()

    try:
        payload = json.loads(
            path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return empty_cache_state()

    if not isinstance(payload, dict):
        return empty_cache_state()

    entries = payload.get("entries", {})

    if not isinstance(entries, dict):
        payload["entries"] = {}

    payload.setdefault(
        "schema_version",
        BUILD_CACHE_SCHEMA_VERSION,
    )
    payload.setdefault(
        "hash_algorithm",
        HASH_ALGORITHM,
    )

    return payload


def write_build_cache(
    state: Mapping[str, Any],
    path: Path = BUILD_CACHE_JSON,
) -> None:
    """Persist build-cache state atomically."""
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


def empty_cache_state() -> dict[str, Any]:
    return {
        "schema_version": (
            BUILD_CACHE_SCHEMA_VERSION
        ),
        "hash_algorithm": HASH_ALGORITHM,
        "entries": {},
    }


def job_command_signature(
    job_id: str,
) -> dict[str, Any]:
    """Build canonical command and job-configuration identity."""
    job = JOB_MAP[
        str(job_id)
    ]

    resolved_command = list(
        resolve_registered_command(
            job.job_id
        )
    )

    return {
        "job_id": job.job_id,
        "command": resolved_command,
        "output_path": str(
            normalize_path(
                job.output_path
            )
        ),
        "dependencies": list(
            job.dependencies
        ),
        "priority": str(
            job.priority
        ),
        "stale_after_hours": float(
            job.stale_after_hours
        ),
        "enabled": bool(
            job.enabled
        ),
        "category": str(
            job.category
        ),
    }


def required_input_manifest(
    job_id: str,
) -> dict[str, str]:
    """Hash every required input path declared by D.2 lineage."""
    contract = input_contract_for_job(
        job_id
    )

    return {
        str(normalize_path(path)): (
            hash_file(path)
        )
        for path in contract.required_paths
    }


def required_output_manifest(
    job_id: str,
) -> dict[str, str]:
    """Hash every required output path declared by D.1 contracts."""
    contract = contract_for_job(
        job_id
    )

    return {
        str(normalize_path(path)): (
            hash_file(path)
        )
        for path in contract.required_paths
    }


def build_identity_payload(
    job_id: str,
) -> dict[str, Any]:
    """Build the deterministic pre-execution cache identity."""
    return {
        "schema_version": (
            BUILD_CACHE_SCHEMA_VERSION
        ),
        "job": job_command_signature(
            job_id
        ),
        "required_inputs": (
            required_input_manifest(
                job_id
            )
        ),
    }


def build_identity_hash(
    job_id: str,
) -> str:
    """Hash canonical command, configuration, and required inputs."""
    payload = build_identity_payload(
        job_id
    )

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


def evaluate_build_cache(
    job_id: str,
    *,
    state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate whether one job can reuse its prior successful outputs."""
    cache_state = (
        dict(state)
        if state is not None
        else load_build_cache()
    )

    entries = cache_state.get(
        "entries",
        {},
    )

    if not isinstance(entries, dict):
        entries = {}

    entry = entries.get(
        str(job_id)
    )

    current_identity = build_identity_hash(
        job_id
    )

    current_inputs = (
        required_input_manifest(
            job_id
        )
    )

    input_validation = (
        validate_job_inputs(
            job_id
        )
    )

    output_validation = (
        validate_job_outputs(
            job_id
        )
    )

    current_outputs = (
        required_output_manifest(
            job_id
        )
    )

    base = {
        "job_id": str(job_id),
        "cache_hit": False,
        "reason": "",
        "identity_hash": (
            current_identity
        ),
        "required_inputs_valid": bool(
            input_validation["success"]
        ),
        "required_outputs_valid": bool(
            output_validation["success"]
        ),
        "required_input_manifest": (
            current_inputs
        ),
        "required_output_manifest": (
            current_outputs
        ),
    }

    if not isinstance(entry, dict):
        base["reason"] = "NO_CACHE_ENTRY"
        return base

    if not input_validation["success"]:
        base["reason"] = (
            "REQUIRED_INPUTS_INVALID"
        )
        return base

    if not output_validation["success"]:
        base["reason"] = (
            "REQUIRED_OUTPUTS_INVALID"
        )
        return base

    cached_identity = str(
        entry.get(
            "identity_hash",
            "",
        )
    )

    if cached_identity != current_identity:
        base["reason"] = (
            "BUILD_IDENTITY_CHANGED"
        )
        return base

    cached_inputs = entry.get(
        "required_input_manifest",
        {},
    )

    if cached_inputs != current_inputs:
        base["reason"] = (
            "INPUT_FINGERPRINTS_CHANGED"
        )
        return base

    cached_outputs = entry.get(
        "required_output_manifest",
        {},
    )

    if cached_outputs != current_outputs:
        base["reason"] = (
            "OUTPUT_FINGERPRINTS_CHANGED"
        )
        return base

    if not all(
        current_outputs.values()
    ):
        base["reason"] = (
            "OUTPUT_FINGERPRINT_MISSING"
        )
        return base

    base["cache_hit"] = True
    base["reason"] = "CACHE_HIT"
    base["cached_run_id"] = str(
        entry.get(
            "run_id",
            "",
        )
    )
    base["cached_at"] = str(
        entry.get(
            "recorded_at",
            "",
        )
    )

    return base


def record_successful_build(
    job_id: str,
    *,
    run_id: str,
    state: Mapping[str, Any] | None = None,
    path: Path = BUILD_CACHE_JSON,
) -> dict[str, Any]:
    """Record one verified successful build in the persistent cache."""
    cache_state = (
        dict(state)
        if state is not None
        else load_build_cache(path)
    )

    entries = cache_state.get(
        "entries",
        {},
    )

    if not isinstance(entries, dict):
        entries = {}

    input_validation = (
        validate_job_inputs(
            job_id
        )
    )

    output_validation = (
        validate_job_outputs(
            job_id
        )
    )

    if not input_validation["success"]:
        raise ValueError(
            "Cannot cache build with invalid "
            f"required inputs: {job_id}"
        )

    if not output_validation["success"]:
        raise ValueError(
            "Cannot cache build with invalid "
            f"required outputs: {job_id}"
        )

    entry = {
        "job_id": str(job_id),
        "run_id": str(run_id),
        "recorded_at": (
            datetime.now(UTC).isoformat()
        ),
        "identity_hash": (
            build_identity_hash(
                job_id
            )
        ),
        "identity_payload": (
            build_identity_payload(
                job_id
            )
        ),
        "required_input_manifest": (
            required_input_manifest(
                job_id
            )
        ),
        "required_output_manifest": (
            required_output_manifest(
                job_id
            )
        ),
    }

    entries = dict(entries)
    entries[
        str(job_id)
    ] = entry

    next_state = {
        "schema_version": (
            BUILD_CACHE_SCHEMA_VERSION
        ),
        "hash_algorithm": HASH_ALGORITHM,
        "entries": entries,
    }

    write_build_cache(
        next_state,
        path=path,
    )

    return entry


def invalidate_build_cache_entry(
    job_id: str,
    *,
    path: Path = BUILD_CACHE_JSON,
) -> bool:
    """Remove one cache entry explicitly."""
    state = load_build_cache(
        path
    )

    entries = state.get(
        "entries",
        {},
    )

    if not isinstance(entries, dict):
        return False

    if str(job_id) not in entries:
        return False

    entries = dict(entries)
    del entries[
        str(job_id)
    ]

    state["entries"] = entries

    write_build_cache(
        state,
        path=path,
    )

    return True


def normalize_path(
    path: Path,
) -> Path:
    return Path(
        str(path).replace(
            "\\",
            "/",
        )
    )


__all__ = [
    "BUILD_CACHE_SCHEMA_VERSION",
    "build_identity_hash",
    "build_identity_payload",
    "empty_cache_state",
    "evaluate_build_cache",
    "invalidate_build_cache_entry",
    "job_command_signature",
    "load_build_cache",
    "record_successful_build",
    "required_input_manifest",
    "required_output_manifest",
    "write_build_cache",
]
