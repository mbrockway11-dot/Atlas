"""Tests for Phase C.4 verified self-healing orchestration."""

from __future__ import annotations

import pandas as pd

from atlas.investment.research_orchestrator.self_healing import (
    annotate_recovery_result,
    blocked_job_ids,
    can_retry,
    schedule_signature,
    verify_job_health,
)


def schedule(
    status: str,
    *,
    job_id: str = "alpha_engines",
) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "job_id": job_id,
            "status": status,
            "reason": f"{status} reason",
            "exists": status != "MISSING",
            "valid": status not in {
                "FAILED",
                "MISSING",
            },
            "fresh": status == "CURRENT",
            "dirty": status in {
                "READY",
                "BLOCKED",
                "STALE",
            },
            "content_stale": False,
            "invalidation_reason": "",
        }
    ])


def test_current_artifact_is_verified_as_healed():
    result = verify_job_health(
        schedule("CURRENT"),
        "alpha_engines",
    )

    assert result["verified"]
    assert result["healed"]
    assert result["status"] == "CURRENT"


def test_ready_artifact_is_not_healed():
    result = verify_job_health(
        schedule("READY"),
        "alpha_engines",
    )

    assert result["verified"]
    assert not result["healed"]


def test_missing_job_is_not_verified():
    result = verify_job_health(
        schedule("CURRENT"),
        "not_registered_here",
    )

    assert not result["verified"]
    assert not result["healed"]
    assert result["status"] == "UNKNOWN"


def test_retry_budget_is_bounded():
    assert can_retry(
        attempts=1,
        max_recovery_attempts=2,
        self_heal=True,
    )

    assert not can_retry(
        attempts=2,
        max_recovery_attempts=2,
        self_heal=True,
    )

    assert not can_retry(
        attempts=1,
        max_recovery_attempts=2,
        self_heal=False,
    )


def test_recovery_result_contains_verification():
    enriched = annotate_recovery_result(
        {
            "job_id": "alpha_engines",
            "status": "SUCCEEDED",
        },
        attempt=2,
        verification={
            "verified": True,
            "healed": False,
            "status": "READY",
            "reason": "Still dirty.",
        },
        retry_pending=True,
        self_heal=True,
    )

    assert enriched[
        "recovery_attempt"
    ] == 2
    assert enriched[
        "artifact_verified"
    ]
    assert not enriched[
        "artifact_healed"
    ]
    assert enriched[
        "retry_pending"
    ]


def test_schedule_signature_is_order_independent():
    first = pd.DataFrame([
        {
            "job_id": "b",
            "status": "BLOCKED",
        },
        {
            "job_id": "a",
            "status": "READY",
        },
    ])

    second = pd.DataFrame([
        {
            "job_id": "a",
            "status": "READY",
        },
        {
            "job_id": "b",
            "status": "BLOCKED",
        },
    ])

    assert (
        schedule_signature(first)
        == schedule_signature(second)
    )


def test_blocked_job_ids_are_reported():
    frame = pd.concat(
        [
            schedule(
                "BLOCKED",
                job_id="b",
            ),
            schedule(
                "CURRENT",
                job_id="a",
            ),
        ],
        ignore_index=True,
    )

    assert blocked_job_ids(
        frame
    ) == ["b"]
