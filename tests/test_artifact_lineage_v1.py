"""Tests for Phase D.2 artifact input-lineage contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.investment import artifact_lineage
from atlas.investment.artifact_lineage import (
    INPUT_CONTRACTS,
    JobInputContract,
    build_lineage_edges,
    input_contract_for_job,
    upstream_job_closure,
    validate_job_inputs,
    validate_lineage_registry,
)
from atlas.investment.research_scheduler import (
    JOBS,
    JOB_MAP,
)


def test_every_job_has_one_input_contract():
    assert len(INPUT_CONTRACTS) == len(JOBS)

    assert {
        contract.job_id
        for contract in INPUT_CONTRACTS
    } == {
        job.job_id
        for job in JOBS
    }


def test_lineage_registry_is_structurally_valid():
    assert validate_lineage_registry() == []


def test_unknown_input_contract_is_rejected():
    with pytest.raises(
        KeyError,
        match="Unknown input-lineage job",
    ):
        input_contract_for_job(
            "not_a_real_job"
        )


def test_dependency_primary_outputs_are_inherited():
    contract = input_contract_for_job(
        "macro_regime_fusion"
    )

    expected = {
        JOB_MAP[
            dependency_id
        ].output_path
        for dependency_id
        in JOB_MAP[
            "macro_regime_fusion"
        ].dependencies
    }

    assert expected.issubset(
        set(contract.required_paths)
    )


def test_upstream_closure_is_transitive():
    closure = upstream_job_closure(
        "research_experiment_execution"
    )

    assert (
        "research_experiment_designer"
        in closure
    )
    assert (
        "research_program_manager"
        in closure
    )
    assert (
        "research_candidate_consolidator"
        in closure
    )


def test_explicit_artifact_lineage_has_producer():
    edges = build_lineage_edges()

    explicit = [
        edge
        for edge in edges
        if edge["artifact_key"]
    ]

    assert explicit
    assert all(
        edge["producer_job_id"]
        for edge in explicit
    )


def test_no_lineage_edge_self_consumes():
    for edge in build_lineage_edges():
        assert (
            edge["producer_job_id"]
            != edge["consumer_job_id"]
        )


def test_missing_required_input_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    fake_primary = (
        tmp_path / "producer.json"
    )

    fake_job = type(
        "FakeJob",
        (),
        {
            "job_id": "fake_consumer",
            "dependencies": (),
            "output_path": (
                tmp_path / "consumer.json"
            ),
        },
    )()

    monkeypatch.setitem(
        artifact_lineage.JOB_MAP,
        "fake_consumer",
        fake_job,
    )

    monkeypatch.setitem(
        artifact_lineage.ARTIFACTS,
        "fake_input",
        fake_primary,
    )

    fake_contract = JobInputContract(
        job_id="fake_consumer",
        required_artifact_keys=(
            "fake_input",
        ),
        inherit_dependency_primary_outputs=False,
    )

    monkeypatch.setitem(
        artifact_lineage.INPUT_CONTRACT_MAP,
        "fake_consumer",
        fake_contract,
    )

    result = validate_job_inputs(
        "fake_consumer"
    )

    assert not result["success"]
    assert (
        result[
            "missing_or_invalid_required_count"
        ]
        == 1
    )

    fake_primary.write_text(
        '{"success": true}',
        encoding="utf-8",
    )

    result = validate_job_inputs(
        "fake_consumer"
    )

    assert result["success"]


def test_required_and_optional_paths_are_deduplicated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    shared = tmp_path / "shared.csv"

    fake_job = type(
        "FakeJob",
        (),
        {
            "job_id": "fake_job",
            "dependencies": (),
            "output_path": (
                tmp_path / "output.json"
            ),
        },
    )()

    monkeypatch.setitem(
        artifact_lineage.JOB_MAP,
        "fake_job",
        fake_job,
    )

    monkeypatch.setitem(
        artifact_lineage.ARTIFACTS,
        "shared_a",
        shared,
    )

    monkeypatch.setitem(
        artifact_lineage.ARTIFACTS,
        "shared_b",
        shared,
    )

    contract = JobInputContract(
        job_id="fake_job",
        required_artifact_keys=(
            "shared_a",
            "shared_b",
        ),
        inherit_dependency_primary_outputs=False,
    )

    assert contract.required_paths == (
        shared,
    )
