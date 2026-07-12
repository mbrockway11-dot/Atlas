"""Tests for Atlas Research Knowledge Graph v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.research_knowledge_graph.builder import (
    build_knowledge_graph,
)
from atlas.investment.research_knowledge_graph.identity import (
    edge_id,
    node_id,
)
from atlas.investment.research_knowledge_graph.integrity import (
    build_graph_metrics,
    build_integrity_report,
)
from atlas.investment.research_knowledge_graph.views import (
    build_lineage_views,
)


def sources() -> dict:
    return {
        "experiments": pd.DataFrame([
            {
                "experiment_id": "EXP-HYP",
                "experiment_type": (
                    "HYPOTHESIS"
                ),
                "natural_key": "HYP-ONE",
                "title": "Drawdown gate",
                "description": (
                    "Restrict signals in deep drawdown."
                ),
                "current_status": "VALIDATED",
                "parent_engine_id": (
                    "momentum_v1"
                ),
                "hypothesis_id": "HYP-ONE",
                "variant_id": "",
                "latest_state_hash": (
                    "a" * 64
                ),
                "latest_source": (
                    "hypothesis_validation"
                ),
                "production_eligible": False,
            },
            {
                "experiment_id": "EXP-VAR",
                "experiment_type": (
                    "VALIDATED_VARIANT"
                ),
                "natural_key": "VAR-ONE",
                "title": "Drawdown-gated momentum",
                "description": (
                    "ALLOW_SIGNAL = drawdown == LOW"
                ),
                "current_status": "APPROVED",
                "parent_engine_id": (
                    "momentum_v1"
                ),
                "hypothesis_id": "HYP-ONE",
                "variant_id": "VAR-ONE",
                "latest_state_hash": (
                    "a" * 64
                ),
                "latest_source": (
                    "variant_decisions"
                ),
                "production_eligible": False,
            },
            {
                "experiment_id": "EXP-RUN",
                "experiment_type": (
                    "RESEARCH_CYCLE"
                ),
                "natural_key": "ORCH-ONE",
                "title": "Research cycle",
                "description": "",
                "current_status": "COMPLETED",
                "parent_engine_id": "",
                "hypothesis_id": "",
                "variant_id": "",
                "latest_state_hash": (
                    "a" * 64
                ),
                "latest_source": (
                    "research_orchestrator"
                ),
                "production_eligible": False,
            },
        ]),
        "relationships": pd.DataFrame([
            {
                "from_experiment_id": (
                    "EXP-HYP"
                ),
                "relationship_type": (
                    "GENERATED_VARIANT"
                ),
                "to_experiment_id": (
                    "EXP-VAR"
                ),
                "source_name": (
                    "validated_variants"
                ),
                "evidence_hash": "abc",
            }
        ]),
        "variant_decisions": pd.DataFrame([
            {
                "variant_id": "VAR-ONE",
                "manual_decision": "APPROVED",
                "manual_reviewer": "Michael",
                "manual_rationale": (
                    "Validation passed."
                ),
                "approval_version": "v1",
            }
        ]),
        "implementation_plans": pd.DataFrame([
            {
                "plan_id": "PLAN-ONE",
                "variant_id": "VAR-ONE",
                "variant_name": (
                    "Drawdown-gated momentum"
                ),
                "plan_status": "PLANNED",
                "parent_engine_id": (
                    "momentum_v1"
                ),
                "hypothesis_id": "HYP-ONE",
                "gate_expression": (
                    "ALLOW_SIGNAL = drawdown == LOW"
                ),
            }
        ]),
        "compiler_report": {
            "state_hash": "a" * 64,
        },
    }


def test_node_ids_are_deterministic():
    assert (
        node_id(
            "HYPOTHESIS",
            "HYP-ONE",
        )
        == node_id(
            "HYPOTHESIS",
            "HYP-ONE",
        )
    )


def test_edge_ids_are_deterministic():
    assert (
        edge_id(
            "A",
            "PRODUCED_VARIANT",
            "B",
        )
        == edge_id(
            "A",
            "PRODUCED_VARIANT",
            "B",
        )
    )


def test_graph_builds_core_node_types():
    graph = build_knowledge_graph(
        sources()
    )

    types = set(
        graph["nodes"][
            "node_type"
        ]
    )

    assert "ENGINE" in types
    assert "HYPOTHESIS" in types
    assert "VARIANT" in types
    assert "DECISION" in types
    assert "IMPLEMENTATION_PLAN" in types
    assert "RESEARCH_CYCLE" in types
    assert "ATLAS_STATE" in types


def test_graph_builds_lineage_edges():
    graph = build_knowledge_graph(
        sources()
    )

    edge_types = set(
        graph["edges"][
            "relationship_type"
        ]
    )

    assert "GENERATED_HYPOTHESIS" in edge_types
    assert "PRODUCED_VARIANT" in edge_types
    assert "RECEIVED_DECISION" in edge_types
    assert "AUTHORIZED_PLAN" in edge_types
    assert "COMPILED_AGAINST" in edge_types


def test_integrity_passes():
    graph = build_knowledge_graph(
        sources()
    )

    integrity = build_integrity_report(
        graph["nodes"],
        graph["edges"],
    )

    assert integrity[
        "passed"
    ].astype(bool).all()


def test_metrics_include_degree_counts():
    graph = build_knowledge_graph(
        sources()
    )

    metrics = build_graph_metrics(
        graph["nodes"],
        graph["edges"],
    )

    assert "in_degree" in metrics.columns
    assert "out_degree" in metrics.columns
    assert "total_degree" in metrics.columns


def test_lineage_views_are_created():
    graph = build_knowledge_graph(
        sources()
    )

    views = build_lineage_views(
        graph["nodes"],
        graph["edges"],
    )

    assert not views[
        "engine_relationships"
    ].empty

    assert not views[
        "hypothesis_relationships"
    ].empty

    assert not views[
        "variant_lineage"
    ].empty

    assert not views[
        "research_cycle_lineage"
    ].empty


def test_graph_never_authorizes_execution():
    graph = build_knowledge_graph(
        sources()
    )

    assert not graph[
        "nodes"
    ][
        "execution_instruction"
    ].astype(bool).any()

    assert not graph[
        "edges"
    ][
        "execution_instruction"
    ].astype(bool).any()

    assert not graph[
        "nodes"
    ][
        "production_eligible"
    ].astype(bool).any()
