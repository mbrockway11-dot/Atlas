"""Atlas Research Scheduler dependency resolution."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

import pandas as pd

from atlas.investment.research_scheduler.config import (
    PRIORITY_ORDER,
)
from atlas.investment.research_scheduler.registry import (
    JOBS,
    JOB_MAP,
)


SCHEDULE_COLUMNS = [
    "schedule_rank",
    "job_id",
    "title",
    "category",
    "priority",
    "priority_rank",
    "status",
    "reason",
    "command",
    "output_path",
    "dependencies",
    "blocking_dependencies",
    "exists",
    "valid",
    "fresh",
    "upstream_newer",
    "incrementally_stale",
    "newer_dependencies",
    "newest_upstream_modified_at",
    "directly_dirty",
    "propagated_dirty",
    "dirty",
    "dirty_dependencies",
    "dirty_roots",
    "dirty_depth",
    "invalidation_reason",
    "age_hours",
    "stale_after_hours",
    "artifact_success",
    "execution_authorized",
    "execution_instruction",
]


def build_research_schedule(
    freshness_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    """Build the deterministic research agenda."""
    freshness_map = {
        row["job_id"]: row
        for row in freshness_rows
    }

    base_status = {}

    for job in JOBS:
        freshness = freshness_map.get(
            job.job_id,
            {},
        )

        if not job.enabled:
            status = "DISABLED"
            reason = (
                "Job is disabled in the registry."
            )
        elif not bool(
            freshness.get(
                "exists",
                False,
            )
        ):
            status = "MISSING"
            reason = (
                "Required output artifact does not exist."
            )
        elif not bool(
            freshness.get(
                "valid",
                False,
            )
        ):
            status = "FAILED"
            reason = (
                freshness.get(
                    "error"
                )
                or "Artifact is invalid."
            )
        elif freshness.get(
            "artifact_success"
        ) is False:
            status = "FAILED"
            reason = (
                "Artifact reports success=False."
            )
        elif (
            bool(
                freshness.get(
                    "dirty",
                    False,
                )
            )
            or bool(
                freshness.get(
                    "incrementally_stale",
                    False,
                )
            )
        ):
            status = "STALE"
            invalidation_reason = str(
                freshness.get(
                    "invalidation_reason",
                    "",
                )
            )
            dirty_roots = str(
                freshness.get(
                    "dirty_roots",
                    "",
                )
            )
            dirty_dependencies = str(
                freshness.get(
                    "dirty_dependencies",
                    "",
                )
            )

            if invalidation_reason == "UPSTREAM_NEWER":
                reason = (
                    "One or more upstream artifacts are "
                    "newer than this output."
                )
            elif invalidation_reason == "UPSTREAM_DIRTY":
                reason = (
                    "A dirty upstream dependency invalidated "
                    "this downstream output."
                )
            else:
                reason = (
                    "Artifact requires rebuilding because of "
                    f"{invalidation_reason or 'DIRTY_STATE'}."
                )

            if dirty_dependencies:
                reason += (
                    " Dirty dependencies: "
                    f"{dirty_dependencies}."
                )

            if dirty_roots:
                reason += (
                    " Dirty roots: "
                    f"{dirty_roots}."
                )
        elif not bool(
            freshness.get(
                "fresh",
                False,
            )
        ):
            status = "STALE"
            reason = (
                "Output artifact exceeded its "
                "freshness threshold."
            )
        else:
            status = "CURRENT"
            reason = (
                "Output artifact is valid and current."
            )

        base_status[
            job.job_id
        ] = {
            "status": status,
            "reason": reason,
        }

    rows = []

    for job in JOBS:
        freshness = freshness_map.get(
            job.job_id,
            {},
        )

        initial = base_status[
            job.job_id
        ]

        status = initial[
            "status"
        ]

        reason = initial[
            "reason"
        ]

        blocking_dependencies = []

        if status in {
            "MISSING",
            "STALE",
            "FAILED",
        }:
            for dependency_id in (
                job.dependencies
            ):
                dependency_status = (
                    base_status[
                        dependency_id
                    ][
                        "status"
                    ]
                )

                if dependency_status not in {
                    "CURRENT",
                }:
                    blocking_dependencies.append(
                        dependency_id
                    )

            if blocking_dependencies:
                status = "BLOCKED"
                reason = (
                    "Upstream dependencies require "
                    "attention before this job."
                )
            else:
                status = "READY"

        rows.append({
            "job_id": job.job_id,
            "title": job.title,
            "category": job.category,
            "priority": job.priority,
            "priority_rank": (
                PRIORITY_ORDER[
                    job.priority
                ]
            ),
            "status": status,
            "reason": reason,
            "command": job.command,
            "output_path": str(
                job.output_path
            ),
            "dependencies": "|".join(
                job.dependencies
            ),
            "blocking_dependencies": "|".join(
                blocking_dependencies
            ),
            "exists": bool(
                freshness.get(
                    "exists",
                    False,
                )
            ),
            "valid": bool(
                freshness.get(
                    "valid",
                    False,
                )
            ),
            "fresh": bool(
                freshness.get(
                    "fresh",
                    False,
                )
            ),
            "upstream_newer": bool(
                freshness.get(
                    "upstream_newer",
                    False,
                )
            ),
            "incrementally_stale": bool(
                freshness.get(
                    "incrementally_stale",
                    False,
                )
            ),
            "newer_dependencies": str(
                freshness.get(
                    "newer_dependencies",
                    "",
                )
            ),
            "newest_upstream_modified_at": str(
                freshness.get(
                    "newest_upstream_modified_at",
                    "",
                )
            ),
            "directly_dirty": bool(
                freshness.get(
                    "directly_dirty",
                    False,
                )
            ),
            "propagated_dirty": bool(
                freshness.get(
                    "propagated_dirty",
                    False,
                )
            ),
            "dirty": bool(
                freshness.get(
                    "dirty",
                    False,
                )
            ),
            "dirty_dependencies": str(
                freshness.get(
                    "dirty_dependencies",
                    "",
                )
            ),
            "dirty_roots": str(
                freshness.get(
                    "dirty_roots",
                    "",
                )
            ),
            "dirty_depth": int(
                freshness.get(
                    "dirty_depth",
                    0,
                )
                or 0
            ),
            "invalidation_reason": str(
                freshness.get(
                    "invalidation_reason",
                    "",
                )
            ),
            "age_hours": freshness.get(
                "age_hours"
            ),
            "stale_after_hours": (
                job.stale_after_hours
            ),
            "artifact_success": (
                freshness.get(
                    "artifact_success"
                )
            ),
            "execution_authorized": False,
            "execution_instruction": False,
        })

    frame = pd.DataFrame(
        rows
    )

    dependency_order = (
        topological_order()
    )

    order_map = {
        job_id: index
        for index, job_id in enumerate(
            dependency_order,
            start=1,
        )
    }

    frame[
        "dependency_order"
    ] = frame[
        "job_id"
    ].map(order_map)

    frame[
        "action_rank"
    ] = frame[
        "status"
    ].map({
        "READY": 1,
        "FAILED": 2,
        "MISSING": 3,
        "STALE": 4,
        "BLOCKED": 5,
        "CURRENT": 6,
        "DISABLED": 7,
    }).fillna(99)

    frame = frame.sort_values(
        [
            "action_rank",
            "priority_rank",
            "dependency_order",
            "job_id",
        ],
        kind="stable",
    ).reset_index(drop=True)

    frame.insert(
        0,
        "schedule_rank",
        range(
            1,
            len(frame) + 1,
        ),
    )

    return frame[
        SCHEDULE_COLUMNS
    ]


def topological_order() -> list[str]:
    """Return a deterministic topological job ordering."""
    indegree = {
        job.job_id: 0
        for job in JOBS
    }

    dependents = defaultdict(list)

    for job in JOBS:
        for dependency in (
            job.dependencies
        ):
            if dependency not in indegree:
                raise ValueError(
                    "Unknown scheduler dependency: "
                    f"{dependency}"
                )

            indegree[
                job.job_id
            ] += 1

            dependents[
                dependency
            ].append(
                job.job_id
            )

    ready = deque(
        sorted(
            job_id
            for job_id, degree in (
                indegree.items()
            )
            if degree == 0
        )
    )

    ordered = []

    while ready:
        current = ready.popleft()

        ordered.append(current)

        for dependent in sorted(
            dependents[current]
        ):
            indegree[
                dependent
            ] -= 1

            if (
                indegree[
                    dependent
                ]
                == 0
            ):
                ready.append(
                    dependent
                )

    if len(ordered) != len(JOBS):
        raise ValueError(
            "Scheduler dependency graph contains a cycle."
        )

    return ordered


def build_dependency_graph() -> pd.DataFrame:
    """Build one row per dependency edge."""
    rows = []

    for job in JOBS:
        if not job.dependencies:
            rows.append({
                "upstream_job_id": "",
                "downstream_job_id": (
                    job.job_id
                ),
                "dependency_type": "ROOT",
                "required": True,
            })
            continue

        for dependency in (
            job.dependencies
        ):
            rows.append({
                "upstream_job_id": (
                    dependency
                ),
                "downstream_job_id": (
                    job.job_id
                ),
                "dependency_type": (
                    "REQUIRES"
                ),
                "required": True,
            })

    return pd.DataFrame(rows)
