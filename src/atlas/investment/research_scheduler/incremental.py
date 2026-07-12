"""Incremental invalidation for the canonical Atlas research DAG.

This module does not own a second graph or registry. It evaluates dependency
edges already defined by the canonical research job registry.

Phase C.1:
    Detect a directly stale downstream artifact when a valid upstream artifact
    is newer than it.

Phase C.2:
    Propagate dirtiness through the complete affected downstream subgraph, even
    when a descendant's immediate dependency artifact has not yet been rebuilt.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping, Sequence

from atlas.investment.research_scheduler.registry import (
    JOBS,
    ResearchJobSpec,
)


def apply_incremental_freshness(
    freshness_rows: Iterable[Mapping[str, Any]],
    *,
    jobs: Sequence[ResearchJobSpec] = JOBS,
) -> list[dict[str, Any]]:
    """Apply direct timestamp invalidation and transitive dirty propagation."""
    rows = [
        dict(row)
        for row in freshness_rows
    ]

    row_map = {
        str(row.get("job_id", "")): row
        for row in rows
        if str(row.get("job_id", ""))
    }

    apply_direct_invalidation(
        row_map=row_map,
        jobs=jobs,
    )

    propagate_dirty_set(
        row_map=row_map,
        jobs=jobs,
    )

    for row in rows:
        apply_default_fields(row)

    return rows


def apply_direct_invalidation(
    *,
    row_map: dict[str, dict[str, Any]],
    jobs: Sequence[ResearchJobSpec],
) -> None:
    """Detect direct upstream-newer invalidation for every registered job."""
    for job in jobs:
        row = row_map.get(job.job_id)

        if row is None:
            continue

        downstream_modified = parse_modified_at(
            row.get("modified_at")
        )

        newer_dependencies: list[str] = []
        newest_upstream: datetime | None = None

        for dependency_id in job.dependencies:
            dependency_row = row_map.get(
                dependency_id
            )

            if not dependency_row:
                continue

            if not bool(
                dependency_row.get(
                    "exists",
                    False,
                )
            ):
                continue

            if not bool(
                dependency_row.get(
                    "valid",
                    False,
                )
            ):
                continue

            upstream_modified = parse_modified_at(
                dependency_row.get(
                    "modified_at"
                )
            )

            if upstream_modified is None:
                continue

            if downstream_modified is None:
                continue

            if upstream_modified <= downstream_modified:
                continue

            newer_dependencies.append(
                dependency_id
            )

            if (
                newest_upstream is None
                or upstream_modified
                > newest_upstream
            ):
                newest_upstream = (
                    upstream_modified
                )

        row["upstream_newer"] = bool(
            newer_dependencies
        )
        row["incrementally_stale"] = bool(
            newer_dependencies
        )
        row["newer_dependencies"] = "|".join(
            newer_dependencies
        )
        row[
            "newest_upstream_modified_at"
        ] = (
            newest_upstream.isoformat()
            if newest_upstream is not None
            else ""
        )


def propagate_dirty_set(
    *,
    row_map: dict[str, dict[str, Any]],
    jobs: Sequence[ResearchJobSpec],
) -> None:
    """Propagate dirty state across all downstream dependency paths.

    Direct dirty roots include artifacts that are missing, invalid, failed,
    age-stale, or directly invalidated by a newer upstream artifact.

    Propagation reaches a fixed point, making behavior independent of registry
    declaration order while still using only canonical registry dependencies.
    """
    job_map = {
        job.job_id: job
        for job in jobs
    }

    dirty: set[str] = set()
    dirty_roots: dict[str, set[str]] = {}
    dirty_depth: dict[str, int] = {}
    direct_reasons: dict[str, str] = {}

    for job in jobs:
        row = row_map.get(job.job_id)

        if row is None or not job.enabled:
            continue

        reason = direct_dirty_reason(row)

        if not reason:
            continue

        dirty.add(job.job_id)
        dirty_roots[job.job_id] = {
            job.job_id
        }
        dirty_depth[job.job_id] = 0
        direct_reasons[job.job_id] = reason

    changed = True

    while changed:
        changed = False

        for job in jobs:
            if (
                not job.enabled
                or job.job_id in dirty
                or job.job_id not in row_map
            ):
                continue

            dirty_dependencies = [
                dependency_id
                for dependency_id
                in job.dependencies
                if dependency_id in dirty
            ]

            if not dirty_dependencies:
                continue

            dirty.add(job.job_id)

            roots: set[str] = set()
            parent_depths: list[int] = []

            for dependency_id in (
                dirty_dependencies
            ):
                roots.update(
                    dirty_roots.get(
                        dependency_id,
                        {dependency_id},
                    )
                )
                parent_depths.append(
                    dirty_depth.get(
                        dependency_id,
                        0,
                    )
                )

            dirty_roots[job.job_id] = roots
            dirty_depth[job.job_id] = (
                max(parent_depths) + 1
            )
            changed = True

    for job_id, row in row_map.items():
        job = job_map.get(job_id)

        if job is None:
            apply_default_fields(row)
            continue

        dirty_dependencies = [
            dependency_id
            for dependency_id in job.dependencies
            if dependency_id in dirty
        ]

        is_dirty = job_id in dirty
        is_direct = (
            job_id in direct_reasons
        )
        is_propagated = bool(
            is_dirty and not is_direct
        )

        row["directly_dirty"] = is_direct
        row["propagated_dirty"] = (
            is_propagated
        )
        row["dirty"] = is_dirty
        row["dirty_dependencies"] = "|".join(
            dirty_dependencies
        )
        row["dirty_roots"] = "|".join(
            sorted(
                dirty_roots.get(
                    job_id,
                    set(),
                )
            )
        )
        row["dirty_depth"] = int(
            dirty_depth.get(
                job_id,
                0,
            )
        )

        if is_direct:
            row["invalidation_reason"] = (
                direct_reasons[job_id]
            )
        elif is_propagated:
            row["invalidation_reason"] = (
                "UPSTREAM_DIRTY"
            )
        else:
            row["invalidation_reason"] = ""


def direct_dirty_reason(
    row: Mapping[str, Any],
) -> str:
    """Return the direct invalidation reason for one artifact row."""
    if not bool(
        row.get("exists", False)
    ):
        return "ARTIFACT_MISSING"

    if not bool(
        row.get("valid", False)
    ):
        return "ARTIFACT_INVALID"

    if row.get("artifact_success") is False:
        return "ARTIFACT_REPORTS_FAILURE"

    if bool(
        row.get(
            "incrementally_stale",
            False,
        )
    ):
        return "UPSTREAM_NEWER"

    if not bool(
        row.get("fresh", False)
    ):
        return "AGE_STALE"

    return ""


def apply_default_fields(
    row: dict[str, Any],
) -> None:
    """Ensure every freshness row exposes the complete incremental contract."""
    defaults = {
        "upstream_newer": False,
        "incrementally_stale": False,
        "newer_dependencies": "",
        "newest_upstream_modified_at": "",
        "directly_dirty": False,
        "propagated_dirty": False,
        "dirty": False,
        "dirty_dependencies": "",
        "dirty_roots": "",
        "dirty_depth": 0,
        "invalidation_reason": "",
    }

    for key, value in defaults.items():
        row.setdefault(key, value)


def parse_modified_at(
    value: Any,
) -> datetime | None:
    """Parse one scheduler modification timestamp safely."""
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    try:
        return datetime.fromisoformat(
            text.replace(
                "Z",
                "+00:00",
            )
        )
    except ValueError:
        return None


__all__ = [
    "apply_incremental_freshness",
    "apply_direct_invalidation",
    "direct_dirty_reason",
    "parse_modified_at",
    "propagate_dirty_set",
]
