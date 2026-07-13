"""Tests for artifact-lineage audit construction."""

from __future__ import annotations

from atlas.investment.artifact_lineage import (
    build_lineage_audit,
)


def test_lineage_audit_reports_all_jobs():
    audit = build_lineage_audit()

    assert audit["success"]
    assert (
        audit["input_contract_count"]
        == audit["registered_job_count"]
    )
    assert audit["lineage_edge_count"] > 0


def test_lineage_edges_have_required_fields():
    audit = build_lineage_audit()

    required = {
        "producer_job_id",
        "consumer_job_id",
        "artifact_key",
        "artifact_path",
        "requirement",
        "lineage_source",
        "direct_dependency",
    }

    for edge in audit["edges"]:
        assert required.issubset(edge)
