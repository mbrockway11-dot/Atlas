"""Tests for Phase D.3 deterministic build caching."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.investment.research_orchestrator import (
    build_cache,
)


def test_cache_state_round_trip(
    tmp_path: Path,
):
    path = tmp_path / "cache.json"

    state = {
        "schema_version": "1.0.0",
        "hash_algorithm": "sha256",
        "entries": {
            "alpha": {
                "identity_hash": "abc",
            }
        },
    }

    build_cache.write_build_cache(
        state,
        path=path,
    )

    assert build_cache.load_build_cache(
        path
    ) == state


def test_no_entry_is_cache_miss(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        build_cache,
        "build_identity_hash",
        lambda job_id: "identity",
    )

    monkeypatch.setattr(
        build_cache,
        "required_input_manifest",
        lambda job_id: {
            "input": "input-hash",
        },
    )

    monkeypatch.setattr(
        build_cache,
        "required_output_manifest",
        lambda job_id: {
            "output": "output-hash",
        },
    )

    monkeypatch.setattr(
        build_cache,
        "validate_job_inputs",
        lambda job_id: {
            "success": True,
        },
    )

    monkeypatch.setattr(
        build_cache,
        "validate_job_outputs",
        lambda job_id: {
            "success": True,
        },
    )

    decision = (
        build_cache.evaluate_build_cache(
            "alpha",
            state={
                "entries": {},
            },
        )
    )

    assert not decision["cache_hit"]
    assert (
        decision["reason"]
        == "NO_CACHE_ENTRY"
    )


def test_matching_entry_is_cache_hit(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        build_cache,
        "build_identity_hash",
        lambda job_id: "identity",
    )

    monkeypatch.setattr(
        build_cache,
        "required_input_manifest",
        lambda job_id: {
            "input": "input-hash",
        },
    )

    monkeypatch.setattr(
        build_cache,
        "required_output_manifest",
        lambda job_id: {
            "output": "output-hash",
        },
    )

    monkeypatch.setattr(
        build_cache,
        "validate_job_inputs",
        lambda job_id: {
            "success": True,
        },
    )

    monkeypatch.setattr(
        build_cache,
        "validate_job_outputs",
        lambda job_id: {
            "success": True,
        },
    )

    state = {
        "entries": {
            "alpha": {
                "identity_hash": (
                    "identity"
                ),
                "required_input_manifest": {
                    "input": "input-hash",
                },
                "required_output_manifest": {
                    "output": "output-hash",
                },
                "run_id": "ORCH-1",
            }
        }
    }

    decision = (
        build_cache.evaluate_build_cache(
            "alpha",
            state=state,
        )
    )

    assert decision["cache_hit"]
    assert (
        decision["reason"]
        == "CACHE_HIT"
    )
    assert (
        decision["cached_run_id"]
        == "ORCH-1"
    )


def test_input_change_is_cache_miss(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        build_cache,
        "build_identity_hash",
        lambda job_id: "new-identity",
    )

    monkeypatch.setattr(
        build_cache,
        "required_input_manifest",
        lambda job_id: {
            "input": "new-hash",
        },
    )

    monkeypatch.setattr(
        build_cache,
        "required_output_manifest",
        lambda job_id: {
            "output": "same-output",
        },
    )

    monkeypatch.setattr(
        build_cache,
        "validate_job_inputs",
        lambda job_id: {
            "success": True,
        },
    )

    monkeypatch.setattr(
        build_cache,
        "validate_job_outputs",
        lambda job_id: {
            "success": True,
        },
    )

    decision = (
        build_cache.evaluate_build_cache(
            "alpha",
            state={
                "entries": {
                    "alpha": {
                        "identity_hash": (
                            "old-identity"
                        ),
                        "required_input_manifest": {
                            "input": "old-hash",
                        },
                        "required_output_manifest": {
                            "output": (
                                "same-output"
                            ),
                        },
                    }
                }
            },
        )
    )

    assert not decision["cache_hit"]
    assert (
        decision["reason"]
        == "BUILD_IDENTITY_CHANGED"
    )


def test_output_change_is_cache_miss(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        build_cache,
        "build_identity_hash",
        lambda job_id: "identity",
    )

    monkeypatch.setattr(
        build_cache,
        "required_input_manifest",
        lambda job_id: {
            "input": "same-input",
        },
    )

    monkeypatch.setattr(
        build_cache,
        "required_output_manifest",
        lambda job_id: {
            "output": "new-output",
        },
    )

    monkeypatch.setattr(
        build_cache,
        "validate_job_inputs",
        lambda job_id: {
            "success": True,
        },
    )

    monkeypatch.setattr(
        build_cache,
        "validate_job_outputs",
        lambda job_id: {
            "success": True,
        },
    )

    decision = (
        build_cache.evaluate_build_cache(
            "alpha",
            state={
                "entries": {
                    "alpha": {
                        "identity_hash": (
                            "identity"
                        ),
                        "required_input_manifest": {
                            "input": "same-input",
                        },
                        "required_output_manifest": {
                            "output": "old-output",
                        },
                    }
                }
            },
        )
    )

    assert not decision["cache_hit"]
    assert (
        decision["reason"]
        == "OUTPUT_FINGERPRINTS_CHANGED"
    )


def test_invalid_outputs_never_hit_cache(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        build_cache,
        "build_identity_hash",
        lambda job_id: "identity",
    )

    monkeypatch.setattr(
        build_cache,
        "required_input_manifest",
        lambda job_id: {},
    )

    monkeypatch.setattr(
        build_cache,
        "required_output_manifest",
        lambda job_id: {},
    )

    monkeypatch.setattr(
        build_cache,
        "validate_job_inputs",
        lambda job_id: {
            "success": True,
        },
    )

    monkeypatch.setattr(
        build_cache,
        "validate_job_outputs",
        lambda job_id: {
            "success": False,
        },
    )

    decision = (
        build_cache.evaluate_build_cache(
            "alpha",
            state={
                "entries": {
                    "alpha": {
                        "identity_hash": (
                            "identity"
                        ),
                    }
                }
            },
        )
    )

    assert not decision["cache_hit"]
    assert (
        decision["reason"]
        == "REQUIRED_OUTPUTS_INVALID"
    )
