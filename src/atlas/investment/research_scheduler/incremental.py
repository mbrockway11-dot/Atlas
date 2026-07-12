"""Incremental dependency freshness for the canonical research DAG.

This module does not define another graph or registry. It evaluates dependency
edges already owned by the canonical research job registry.

A downstream artifact is incrementally stale when at least one valid upstream
artifact was modified after the downstream artifact.
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
    """Enrich freshness rows with canonical dependency invalidation signals.

    Existing age-based freshness values remain unchanged. The scheduler decides
    whether an incrementally stale artifact should be rebuilt.
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

    for job in jobs:
        row = row_map.get(job.job_id)

        if row is None:
            continue

        downstream_modified = parse_modified_at(
            row.get("modified_at")
        )

        newer_dependencies: list[str] = []
        newest_upstream_modified_at = ""

        for dependency_id in job.dependencies:
            dependency_row = row_map.get(
                dependency_id
            )

            if not dependency_row:
                continue

            if not bool(
                dependency_row.get("exists", False)
            ):
                continue

            if not bool(
                dependency_row.get("valid", False)
            ):
                continue

            upstream_modified = parse_modified_at(
                dependency_row.get("modified_at")
            )

            if upstream_modified is None:
                continue

            if (
                downstream_modified is not None
                and upstream_modified
                > downstream_modified
            ):
                newer_dependencies.append(
                    dependency_id
                )

                if (
                    not newest_upstream_modified_at
                    or upstream_modified
                    > parse_modified_at(
                        newest_upstream_modified_at
                    )
                ):
                    newest_upstream_modified_at = (
                        upstream_modified.isoformat()
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
        ] = newest_upstream_modified_at

    for row in rows:
        row.setdefault(
            "upstream_newer",
            False,
        )
        row.setdefault(
            "incrementally_stale",
            False,
        )
        row.setdefault(
            "newer_dependencies",
            "",
        )
        row.setdefault(
            "newest_upstream_modified_at",
            "",
        )

    return rows


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
    "parse_modified_at",
]
