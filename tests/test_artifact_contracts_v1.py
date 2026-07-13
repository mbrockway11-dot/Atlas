"""Tests for Phase D.1 artifact producer/output contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.investment import artifact_contracts
from atlas.investment.artifact_contracts import (
    CONTRACTS,
    JobArtifactContract,
    contract_for_job,
    inspect_output,
    producer_for_artifact_key,
    validate_contract_registry,
    validate_job_outputs,
)
from atlas.investment.research_scheduler import (
    JOBS,
)


def test_every_job_has_exactly_one_contract():
    assert len(CONTRACTS) == len(JOBS)

    assert {
        contract.job_id
        for contract in CONTRACTS
    } == {
        job.job_id
        for job in JOBS
    }


def test_contract_registry_is_structurally_valid():
    assert validate_contract_registry() == []


def test_primary_output_is_always_required():
    contract = contract_for_job(
        "alpha_engines"
    )

    assert contract.require_primary_output
    assert (
        contract.primary_output_path
        in contract.required_paths
    )


def test_known_secondary_artifact_has_one_producer():
    assert producer_for_artifact_key(
        "research_execution_report"
    ) == "research_experiment_execution"


def test_unknown_contract_job_is_rejected():
    with pytest.raises(
        KeyError,
        match="Unknown artifact contract job",
    ):
        contract_for_job(
            "not_a_job"
        )


def test_valid_json_output_passes(
    tmp_path: Path,
):
    path = tmp_path / "report.json"

    path.write_text(
        json.dumps(
            {
                "success": True,
            }
        ),
        encoding="utf-8",
    )

    result = inspect_output(
        path,
        required=True,
    )

    assert result["exists"]
    assert result["readable"]
    assert result["valid"]


def test_malformed_json_output_fails(
    tmp_path: Path,
):
    path = tmp_path / "report.json"

    path.write_text(
        "{broken",
        encoding="utf-8",
    )

    result = inspect_output(
        path,
        required=True,
    )

    assert not result["valid"]
    assert "JSONDecodeError" in (
        result["error"]
    )


def test_valid_csv_output_passes(
    tmp_path: Path,
):
    path = tmp_path / "table.csv"

    path.write_text(
        "name,value\nalpha,1\n",
        encoding="utf-8",
    )

    result = inspect_output(
        path,
        required=True,
    )

    assert result["valid"]


def test_empty_required_output_fails(
    tmp_path: Path,
):
    path = tmp_path / "empty.csv"
    path.write_text(
        "",
        encoding="utf-8",
    )

    result = inspect_output(
        path,
        required=True,
    )

    assert not result["valid"]
    assert result["error"] == (
        "OUTPUT_EMPTY"
    )


def test_missing_optional_output_is_not_valid_but_identified(
    tmp_path: Path,
):
    path = tmp_path / "optional.csv"

    result = inspect_output(
        path,
        required=False,
    )

    assert not result["exists"]
    assert not result["valid"]
    assert result["error"] == (
        "OPTIONAL_OUTPUT_MISSING"
    )


def test_job_validation_requires_all_required_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    primary = tmp_path / "primary.json"
    secondary = tmp_path / "secondary.csv"

    primary.write_text(
        '{"success": true}',
        encoding="utf-8",
    )

    fake_job = type(
        "FakeJob",
        (),
        {
            "output_path": primary,
        },
    )()

    monkeypatch.setitem(
        artifact_contracts.JOB_MAP,
        "fake_job",
        fake_job,
    )

    monkeypatch.setitem(
        artifact_contracts.ARTIFACTS,
        "fake_secondary",
        secondary,
    )

    fake_contract = JobArtifactContract(
        job_id="fake_job",
        required_artifact_keys=(
            "fake_secondary",
        ),
    )

    monkeypatch.setitem(
        artifact_contracts.CONTRACT_MAP,
        "fake_job",
        fake_contract,
    )

    result = validate_job_outputs(
        "fake_job"
    )

    assert not result["success"]
    assert (
        result[
            "missing_or_invalid_required_count"
        ]
        == 1
    )

    secondary.write_text(
        "name,value\nalpha,1\n",
        encoding="utf-8",
    )

    result = validate_job_outputs(
        "fake_job"
    )

    assert result["success"]
