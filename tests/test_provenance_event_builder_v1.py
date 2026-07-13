"""Tests for provenance event construction."""

from __future__ import annotations

import pytest

from atlas.investment.research_orchestrator import (
    provenance,
)


def test_event_builder_records_cache_and_verification(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        provenance,
        "job_command_signature",
        lambda job_id: {
            "job_id": job_id,
            "command": ["python", "job.py"],
        },
    )

    monkeypatch.setattr(
        provenance,
        "build_identity_hash",
        lambda job_id: "identity",
    )

    monkeypatch.setattr(
        provenance,
        "required_input_manifest",
        lambda job_id: {
            "input.csv": "input-hash",
        },
    )

    monkeypatch.setattr(
        provenance,
        "required_output_manifest",
        lambda job_id: {
            "output.csv": "output-hash",
        },
    )

    fake_contract = type(
        "Contract",
        (),
        {
            "required_paths": (),
            "optional_paths": (),
        },
    )()

    monkeypatch.setattr(
        provenance,
        "input_contract_for_job",
        lambda job_id: fake_contract,
    )

    monkeypatch.setattr(
        provenance,
        "contract_for_job",
        lambda job_id: fake_contract,
    )

    event = (
        provenance.build_provenance_event(
            job_id="alpha",
            run_id="ORCH-1",
            result={
                "status": "CACHED",
                "cache_hit": True,
                "cached_run_id": (
                    "ORCH-OLD"
                ),
                "artifact_verified": True,
                "artifact_healed": True,
            },
            attempt=1,
            cache_decision={
                "cache_hit": True,
                "reason": "CACHE_HIT",
                "cached_run_id": (
                    "ORCH-OLD"
                ),
            },
            verification={
                "verified": True,
                "healed": True,
            },
            recorded_at=(
                "2026-07-12T12:00:00+00:00"
            ),
        )
    )

    assert event["event_id"].startswith(
        "PROV-"
    )
    assert event["cache"]["hit"]
    assert (
        event["cache"][
            "cached_run_id"
        ]
        == "ORCH-OLD"
    )
    assert event["verification"][
        "healed"
    ]
    assert (
        event[
            "required_input_manifest"
        ][
            "input.csv"
        ]
        == "input-hash"
    )
