"""Tests for Phase C.3 persistent content fingerprints."""

from __future__ import annotations

import os
from pathlib import Path

from atlas.investment.research_scheduler.fingerprints import (
    apply_content_fingerprints,
    hash_file,
    load_fingerprint_state,
    write_fingerprint_state,
)
from atlas.investment.research_scheduler.incremental import (
    apply_incremental_freshness,
)
from atlas.investment.research_scheduler.registry import (
    ResearchJobSpec,
)


def job(
    job_id: str,
    path: Path,
    dependencies: tuple[str, ...] = (),
) -> ResearchJobSpec:
    return ResearchJobSpec(
        job_id=job_id,
        title=job_id,
        command=f"python scripts/{job_id}.py",
        output_path=path,
        dependencies=dependencies,
        priority="HIGH",
        stale_after_hours=24.0,
        enabled=True,
        category="test",
    )


def row(
    job_id: str,
    path: Path,
    modified_at: str,
) -> dict:
    return {
        "job_id": job_id,
        "title": job_id,
        "category": "test",
        "output_path": str(path),
        "exists": path.exists(),
        "valid": True,
        "modified_at": modified_at,
        "age_hours": 1.0,
        "stale_after_hours": 24.0,
        "fresh": True,
        "artifact_success": True,
        "artifact_version": "test",
        "error": "",
    }


def by_id(rows: list[dict]) -> dict[str, dict]:
    return {
        item["job_id"]: item
        for item in rows
    }


def test_hash_file_is_deterministic(tmp_path: Path):
    path = tmp_path / "artifact.json"
    path.write_text(
        '{"value": 1}',
        encoding="utf-8",
    )

    first = hash_file(path)
    second = hash_file(path)

    assert first
    assert first == second


def test_touch_without_content_change_does_not_invalidate(
    tmp_path: Path,
):
    upstream_path = tmp_path / "upstream.json"
    downstream_path = tmp_path / "downstream.json"

    upstream_path.write_text(
        '{"value": 1}',
        encoding="utf-8",
    )
    downstream_path.write_text(
        '{"result": 1}',
        encoding="utf-8",
    )

    jobs = (
        job("upstream", upstream_path),
        job(
            "downstream",
            downstream_path,
            ("upstream",),
        ),
    )

    first_rows, state = apply_content_fingerprints(
        [
            row(
                "upstream",
                upstream_path,
                "2026-07-12T12:00:00+00:00",
            ),
            row(
                "downstream",
                downstream_path,
                "2026-07-12T13:00:00+00:00",
            ),
        ],
        jobs=jobs,
        state={},
    )

    os.utime(upstream_path, None)

    second_rows, _ = apply_content_fingerprints(
        [
            row(
                "upstream",
                upstream_path,
                "2026-07-12T14:00:00+00:00",
            ),
            row(
                "downstream",
                downstream_path,
                "2026-07-12T13:00:00+00:00",
            ),
        ],
        jobs=jobs,
        state=state,
    )

    enriched = apply_incremental_freshness(
        second_rows,
        jobs=jobs,
    )

    result = by_id(enriched)

    assert not result["downstream"][
        "content_stale"
    ]
    assert not result["downstream"][
        "incrementally_stale"
    ]
    assert not result["downstream"]["dirty"]


def test_changed_upstream_content_invalidates_downstream(
    tmp_path: Path,
):
    upstream_path = tmp_path / "upstream.json"
    downstream_path = tmp_path / "downstream.json"

    upstream_path.write_text(
        '{"value": 1}',
        encoding="utf-8",
    )
    downstream_path.write_text(
        '{"result": 1}',
        encoding="utf-8",
    )

    jobs = (
        job("upstream", upstream_path),
        job(
            "downstream",
            downstream_path,
            ("upstream",),
        ),
    )

    _, state = apply_content_fingerprints(
        [
            row(
                "upstream",
                upstream_path,
                "2026-07-12T12:00:00+00:00",
            ),
            row(
                "downstream",
                downstream_path,
                "2026-07-12T13:00:00+00:00",
            ),
        ],
        jobs=jobs,
        state={},
    )

    upstream_path.write_text(
        '{"value": 2}',
        encoding="utf-8",
    )

    second_rows, _ = apply_content_fingerprints(
        [
            row(
                "upstream",
                upstream_path,
                "2026-07-12T14:00:00+00:00",
            ),
            row(
                "downstream",
                downstream_path,
                "2026-07-12T13:00:00+00:00",
            ),
        ],
        jobs=jobs,
        state=state,
    )

    enriched = apply_incremental_freshness(
        second_rows,
        jobs=jobs,
    )

    result = by_id(enriched)

    assert result["downstream"][
        "content_stale"
    ]
    assert result["downstream"][
        "content_changed_dependencies"
    ] == "upstream"
    assert result["downstream"]["dirty"]
    assert result["downstream"][
        "invalidation_reason"
    ] == "UPSTREAM_CONTENT_CHANGED"


def test_downstream_rebuild_acknowledges_new_dependency_hash(
    tmp_path: Path,
):
    upstream_path = tmp_path / "upstream.json"
    downstream_path = tmp_path / "downstream.json"

    upstream_path.write_text(
        '{"value": 1}',
        encoding="utf-8",
    )
    downstream_path.write_text(
        '{"result": 1}',
        encoding="utf-8",
    )

    jobs = (
        job("upstream", upstream_path),
        job(
            "downstream",
            downstream_path,
            ("upstream",),
        ),
    )

    _, initial_state = apply_content_fingerprints(
        [
            row(
                "upstream",
                upstream_path,
                "2026-07-12T12:00:00+00:00",
            ),
            row(
                "downstream",
                downstream_path,
                "2026-07-12T13:00:00+00:00",
            ),
        ],
        jobs=jobs,
        state={},
    )

    upstream_path.write_text(
        '{"value": 2}',
        encoding="utf-8",
    )

    stale_rows, stale_state = apply_content_fingerprints(
        [
            row(
                "upstream",
                upstream_path,
                "2026-07-12T14:00:00+00:00",
            ),
            row(
                "downstream",
                downstream_path,
                "2026-07-12T13:00:00+00:00",
            ),
        ],
        jobs=jobs,
        state=initial_state,
    )

    assert by_id(stale_rows)[
        "downstream"
    ]["content_stale"]

    downstream_path.write_text(
        '{"result": 2}',
        encoding="utf-8",
    )

    rebuilt_rows, rebuilt_state = (
        apply_content_fingerprints(
            [
                row(
                    "upstream",
                    upstream_path,
                    "2026-07-12T14:00:00+00:00",
                ),
                row(
                    "downstream",
                    downstream_path,
                    "2026-07-12T15:00:00+00:00",
                ),
            ],
            jobs=jobs,
            state=stale_state,
        )
    )

    rebuilt = by_id(rebuilt_rows)[
        "downstream"
    ]

    assert rebuilt[
        "output_content_changed"
    ]
    assert not rebuilt["content_stale"]

    acknowledged = rebuilt_state[
        "jobs"
    ][
        "downstream"
    ][
        "dependency_hashes"
    ][
        "upstream"
    ]

    assert acknowledged == hash_file(
        upstream_path
    )


def test_fingerprint_state_round_trip(tmp_path: Path):
    path = tmp_path / "state.json"

    state = {
        "schema_version": "1.0.0",
        "hash_algorithm": "sha256",
        "jobs": {
            "a": {
                "output_hash": "abc",
                "dependency_hashes": {},
            }
        },
    }

    write_fingerprint_state(
        state,
        path=path,
    )

    assert load_fingerprint_state(
        path
    ) == state
