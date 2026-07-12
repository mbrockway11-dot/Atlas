"""Tests for Phase C.2 transitive dirty-set propagation."""

from __future__ import annotations

from pathlib import Path

from atlas.investment.research_scheduler.incremental import (
    apply_incremental_freshness,
)
from atlas.investment.research_scheduler.registry import (
    ResearchJobSpec,
)
from atlas.investment.research_scheduler.scheduler import (
    build_research_schedule,
)


def job(
    job_id: str,
    dependencies: tuple[str, ...] = (),
) -> ResearchJobSpec:
    return ResearchJobSpec(
        job_id=job_id,
        title=job_id,
        command=(
            f"python scripts/{job_id}.py"
        ),
        output_path=Path(
            f"output/{job_id}.json"
        ),
        dependencies=dependencies,
        priority="HIGH",
        stale_after_hours=24.0,
        enabled=True,
        category="test",
    )


def row(
    job_id: str,
    modified_at: str,
    *,
    exists: bool = True,
    valid: bool = True,
    fresh: bool = True,
    artifact_success=True,
) -> dict:
    return {
        "job_id": job_id,
        "title": job_id,
        "category": "test",
        "output_path": f"{job_id}.json",
        "exists": exists,
        "valid": valid,
        "modified_at": modified_at,
        "age_hours": 1.0,
        "stale_after_hours": 24.0,
        "fresh": fresh,
        "artifact_success": (
            artifact_success
        ),
        "artifact_version": "test",
        "error": "",
    }


def by_id(rows: list[dict]) -> dict[str, dict]:
    return {
        item["job_id"]: item
        for item in rows
    }


def test_direct_dirty_root_propagates_multiple_hops():
    jobs = (
        job("a"),
        job("b", ("a",)),
        job("c", ("b",)),
        job("d", ("c",)),
    )

    rows = apply_incremental_freshness(
        [
            row(
                "a",
                "2026-07-12T12:00:00+00:00",
                fresh=False,
            ),
            row(
                "b",
                "2026-07-12T13:00:00+00:00",
            ),
            row(
                "c",
                "2026-07-12T15:00:00+00:00",
            ),
            row(
                "d",
                "2026-07-12T16:00:00+00:00",
            ),
        ],
        jobs=jobs,
    )

    result = by_id(rows)

    assert result["a"]["directly_dirty"]
    assert not result["a"]["propagated_dirty"]
    assert result["a"]["dirty_depth"] == 0
    assert result["a"]["dirty_roots"] == "a"

    assert result["b"]["dirty"]
    assert result["b"]["dirty_depth"] == 1
    assert result["b"]["dirty_roots"] == "a"

    assert result["c"]["propagated_dirty"]
    assert result["c"]["dirty_depth"] == 2
    assert result["c"]["dirty_roots"] == "a"

    assert result["d"]["propagated_dirty"]
    assert result["d"]["dirty_depth"] == 3
    assert result["d"]["dirty_roots"] == "a"


def test_unrelated_branch_remains_clean():
    jobs = (
        job("root_a"),
        job("child_a", ("root_a",)),
        job("root_b"),
        job("child_b", ("root_b",)),
    )

    rows = apply_incremental_freshness(
        [
            row(
                "root_a",
                "2026-07-12T12:00:00+00:00",
                valid=False,
            ),
            row(
                "child_a",
                "2026-07-12T12:00:00+00:00",
            ),
            row(
                "root_b",
                "2026-07-12T12:00:00+00:00",
            ),
            row(
                "child_b",
                "2026-07-12T12:00:00+00:00",
            ),
        ],
        jobs=jobs,
    )

    result = by_id(rows)

    assert result["root_a"]["dirty"]
    assert result["child_a"]["dirty"]
    assert not result["root_b"]["dirty"]
    assert not result["child_b"]["dirty"]


def test_multiple_dirty_roots_are_preserved():
    jobs = (
        job("a"),
        job("b"),
        job("merge", ("a", "b")),
        job("leaf", ("merge",)),
    )

    rows = apply_incremental_freshness(
        [
            row(
                "a",
                "2026-07-12T12:00:00+00:00",
                fresh=False,
            ),
            row(
                "b",
                "2026-07-12T12:00:00+00:00",
                artifact_success=False,
            ),
            row(
                "merge",
                "2026-07-12T13:00:00+00:00",
            ),
            row(
                "leaf",
                "2026-07-12T14:00:00+00:00",
            ),
        ],
        jobs=jobs,
    )

    result = by_id(rows)

    assert (
        result["merge"]["dirty_roots"]
        == "a|b"
    )
    assert (
        result["leaf"]["dirty_roots"]
        == "a|b"
    )
    assert (
        result["merge"]["dirty_dependencies"]
        == "a|b"
    )


def test_direct_timestamp_invalidation_becomes_dirty_root():
    jobs = (
        job("upstream"),
        job(
            "downstream",
            ("upstream",),
        ),
        job(
            "leaf",
            ("downstream",),
        ),
    )

    rows = apply_incremental_freshness(
        [
            row(
                "upstream",
                "2026-07-12T14:00:00+00:00",
            ),
            row(
                "downstream",
                "2026-07-12T13:00:00+00:00",
            ),
            row(
                "leaf",
                "2026-07-12T15:00:00+00:00",
            ),
        ],
        jobs=jobs,
    )

    result = by_id(rows)

    assert result["downstream"][
        "incrementally_stale"
    ]
    assert result["downstream"][
        "directly_dirty"
    ]
    assert result["downstream"][
        "invalidation_reason"
    ] == "UPSTREAM_NEWER"

    assert result["leaf"][
        "propagated_dirty"
    ]
    assert result["leaf"][
        "dirty_roots"
    ] == "downstream"


def test_scheduler_executes_root_and_blocks_descendants(
    monkeypatch,
):
    from atlas.investment.research_scheduler import (
        scheduler,
    )

    jobs = (
        job("a"),
        job("b", ("a",)),
        job("c", ("b",)),
    )

    rows = apply_incremental_freshness(
        [
            row(
                "a",
                "2026-07-12T12:00:00+00:00",
                fresh=False,
            ),
            row(
                "b",
                "2026-07-12T13:00:00+00:00",
            ),
            row(
                "c",
                "2026-07-12T14:00:00+00:00",
            ),
        ],
        jobs=jobs,
    )

    monkeypatch.setattr(
        scheduler,
        "JOBS",
        jobs,
    )

    schedule = build_research_schedule(
        rows
    )

    states = {
        item["job_id"]: item["status"]
        for item in schedule.to_dict(
            orient="records"
        )
    }

    assert states == {
        "a": "READY",
        "b": "BLOCKED",
        "c": "BLOCKED",
    }


def test_registry_order_does_not_change_propagation():
    jobs = (
        job("c", ("b",)),
        job("a"),
        job("b", ("a",)),
    )

    rows = apply_incremental_freshness(
        [
            row(
                "a",
                "2026-07-12T12:00:00+00:00",
                exists=False,
            ),
            row(
                "b",
                "2026-07-12T13:00:00+00:00",
            ),
            row(
                "c",
                "2026-07-12T14:00:00+00:00",
            ),
        ],
        jobs=jobs,
    )

    result = by_id(rows)

    assert result["a"]["dirty_depth"] == 0
    assert result["b"]["dirty_depth"] == 1
    assert result["c"]["dirty_depth"] == 2
