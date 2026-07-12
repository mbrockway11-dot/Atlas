"""Atlas Research Knowledge Graph v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "atlas_research_knowledge_graph_v1"
SCHEMA_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_research_knowledge_graph"
)

NODES_CSV = (
    OUTPUT_DIR
    / "knowledge_graph_nodes.csv"
)

EDGES_CSV = (
    OUTPUT_DIR
    / "knowledge_graph_edges.csv"
)

ENGINE_RELATIONSHIPS_CSV = (
    OUTPUT_DIR
    / "engine_relationships.csv"
)

HYPOTHESIS_RELATIONSHIPS_CSV = (
    OUTPUT_DIR
    / "hypothesis_relationships.csv"
)

VARIANT_LINEAGE_CSV = (
    OUTPUT_DIR
    / "variant_lineage.csv"
)

PORTFOLIO_LINEAGE_CSV = (
    OUTPUT_DIR
    / "portfolio_lineage.csv"
)

RESEARCH_CYCLE_LINEAGE_CSV = (
    OUTPUT_DIR
    / "research_cycle_lineage.csv"
)

GRAPH_INTEGRITY_CSV = (
    OUTPUT_DIR
    / "graph_integrity.csv"
)

GRAPH_METRICS_CSV = (
    OUTPUT_DIR
    / "graph_metrics.csv"
)

STATE_JSON = (
    OUTPUT_DIR
    / "knowledge_graph_state.json"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "knowledge_graph_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "knowledge_graph_report.md"
)

SOURCE = VERSION

NODE_TYPES = {
    "ENGINE",
    "HYPOTHESIS",
    "VARIANT",
    "PORTFOLIO_EXPERIMENT",
    "RESEARCH_CYCLE",
    "ATLAS_STATE",
    "DECISION",
    "IMPLEMENTATION_PLAN",
}

EDGE_TYPES = {
    "GENERATED_HYPOTHESIS",
    "PRODUCED_VARIANT",
    "RECEIVED_DECISION",
    "AUTHORIZED_PLAN",
    "EVALUATED_PORTFOLIO",
    "OBSERVED_IN_CYCLE",
    "COMPILED_AGAINST",
    "DERIVED_FROM",
}
