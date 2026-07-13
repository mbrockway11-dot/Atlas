"""Tests for artifact-contract-aware self-healing verification."""

from __future__ import annotations

import pandas as pd

from atlas.investment.research_orchestrator import (
    self_healing,
)


def current_schedule() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "job_id": "alpha_engines",
            "status": "CURRENT",
            "reason": "Current.",
            "exists": True,
            "valid": True,
            "fresh": True,
            "dirty": False,
            "content_stale": False,
            "invalidation_reason": "",
        }
    ])


def test_current_scheduler_state_requires_output_contract(
    monkeypatch,
):
    monkeypatch.setattr(
        self_healing,
        "validate_job_outputs",
        lambda job_id: {
            "job_id": job_id,
            "success": False,
            "required_output_count": 2,
            "valid_required_output_count": 1,
            "missing_or_invalid_required_count": 1,
            "required_failures": [
                {
                    "path": "missing.csv",
                    "error": (
                        "REQUIRED_OUTPUT_MISSING"
                    ),
                }
            ],
        },
    )

    result = (
        self_healing.verify_job_health(
            current_schedule(),
            "alpha_engines",
        )
    )

    assert result["scheduler_healthy"]
    assert not result["contract_healthy"]
    assert not result["healed"]
    assert (
        result[
            "missing_or_invalid_required_count"
        ]
        == 1
    )


def test_current_scheduler_and_valid_contract_are_healed(
    monkeypatch,
):
    monkeypatch.setattr(
        self_healing,
        "validate_job_outputs",
        lambda job_id: {
            "job_id": job_id,
            "success": True,
            "required_output_count": 2,
            "valid_required_output_count": 2,
            "missing_or_invalid_required_count": 0,
            "required_failures": [],
        },
    )

    result = (
        self_healing.verify_job_health(
            current_schedule(),
            "alpha_engines",
        )
    )

    assert result["scheduler_healthy"]
    assert result["contract_healthy"]
    assert result["healed"]
