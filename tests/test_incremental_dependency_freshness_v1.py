"""Tests for Phase C.1 incremental dependency invalidation."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from atlas.investment.research_scheduler.incremental import (
    apply_incremental_freshness,
    parse_modified_at,
)
from atlas.investment.research_scheduler.registry import (
    JOB_MAP,
)
from atlas.investment.research_scheduler.scheduler import (
    build_research_schedule,
)


def freshness_row(
    job_id: str,
    modified_at: str,
    *,
    fresh: bool = True,
) -> dict:
    return {
        "job_id": job_id,
        "title": job_id,
        "category": "test",
        "output_path": f"{job_id}.json",
        "exists": True,
        "valid": True,
        "modified_at": modified_at,
        "age_hours": 1.0,
        "stale_after_hours": 24.0,
        "fresh": fresh,
        "artifact_success": True,
        "artifact_version": "test",
        "error": "",
    }


def test_parse_modified_at_accepts_iso_timestamp():
    parsed = parse_modified_at(
        "2026-07-12T12:00:00+00:00"
    )

    assert parsed is not None
    assert parsed.isoformat() == (
        "2026-07-12T12:00:00+00:00"
    )


def test_root_job_is_not_incrementally_stale():
    alpha = JOB_MAP["alpha_engines"]

    rows = apply_incremental_freshness(
        [
            freshness_row(
                "alpha_engines",
                "2026-07-12T12:00:00+00:00",
            )
        ],
        jobs=(alpha,),
    )

    assert rows[0]["upstream_newer"] is False
    assert (
        rows[0]["incrementally_stale"]
        is False
    )
    assert rows[0]["newer_dependencies"] == ""


def test_newer_upstream_invalidates_downstream():
    alpha = JOB_MAP["alpha_engines"]
    regime = JOB_MAP["regime_intelligence"]

    rows = apply_incremental_freshness(
        [
            freshness_row(
                "alpha_engines",
                "2026-07-12T13:00:00+00:00",
            ),
            freshness_row(
                "regime_intelligence",
                "2026-07-12T12:00:00+00:00",
            ),
        ],
        jobs=(alpha, regime),
    )

    result = {
        row["job_id"]: row
        for row in rows
    }

    assert (
        result["regime_intelligence"][
            "incrementally_stale"
        ]
        is True
    )
    assert (
        result["regime_intelligence"][
            "newer_dependencies"
        ]
        == "alpha_engines"
    )


def test_older_upstream_does_not_invalidate_downstream():
    alpha = JOB_MAP["alpha_engines"]
    regime = JOB_MAP["regime_intelligence"]

    rows = apply_incremental_freshness(
        [
            freshness_row(
                "alpha_engines",
                "2026-07-12T11:00:00+00:00",
            ),
            freshness_row(
                "regime_intelligence",
                "2026-07-12T12:00:00+00:00",
            ),
        ],
        jobs=(alpha, regime),
    )

    result = {
        row["job_id"]: row
        for row in rows
    }

    assert (
        result["regime_intelligence"][
            "incrementally_stale"
        ]
        is False
    )


def test_scheduler_marks_incremental_stale_job_ready():
    rows = []

    for job_id, job in JOB_MAP.items():
        rows.append(
            freshness_row(
                job_id,
                "2026-07-12T12:00:00+00:00",
            )
        )

    for row in rows:
        row.update({
            "upstream_newer": False,
            "incrementally_stale": False,
            "newer_dependencies": "",
            "newest_upstream_modified_at": "",
        })

    regime_row = next(
        row
        for row in rows
        if row["job_id"]
        == "regime_intelligence"
    )

    regime_row.update({
        "upstream_newer": True,
        "incrementally_stale": True,
        "newer_dependencies": (
            "alpha_engines"
        ),
        "newest_upstream_modified_at": (
            "2026-07-12T13:00:00+00:00"
        ),
    })

    schedule = build_research_schedule(
        rows
    )

    regime = schedule[
        schedule["job_id"].eq(
            "regime_intelligence"
        )
    ].iloc[0]

    assert regime["status"] == "READY"
    assert bool(
        regime["incrementally_stale"]
    )
    assert (
        regime["newer_dependencies"]
        == "alpha_engines"
    )


def test_incremental_stale_job_blocks_on_dirty_dependency():
    rows = []

    for job_id, job in JOB_MAP.items():
        rows.append(
            freshness_row(
                job_id,
                "2026-07-12T12:00:00+00:00",
            )
        )

    for row in rows:
        row.update({
            "upstream_newer": False,
            "incrementally_stale": False,
            "newer_dependencies": "",
            "newest_upstream_modified_at": "",
        })

    alpha_row = next(
        row
        for row in rows
        if row["job_id"] == "alpha_engines"
    )
    alpha_row["fresh"] = False

    regime_row = next(
        row
        for row in rows
        if row["job_id"]
        == "regime_intelligence"
    )
    regime_row.update({
        "upstream_newer": True,
        "incrementally_stale": True,
        "newer_dependencies": (
            "alpha_engines"
        ),
    })

    schedule = build_research_schedule(
        rows
    )

    alpha = schedule[
        schedule["job_id"].eq(
            "alpha_engines"
        )
    ].iloc[0]

    regime = schedule[
        schedule["job_id"].eq(
            "regime_intelligence"
        )
    ].iloc[0]

    assert alpha["status"] == "READY"
    assert regime["status"] == "BLOCKED"
    assert (
        regime["blocking_dependencies"]
        == "alpha_engines"
    )
