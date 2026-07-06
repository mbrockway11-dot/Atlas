
"""Atlas Knowledge Graph builder."""

from __future__ import annotations

from typing import Any

from atlas.knowledge.evidence_graph import build_evidence_graph
from atlas.knowledge.hypothesis_registry import register_discovery_hypotheses
from atlas.knowledge.insight_memory import store_discovery_insights
from atlas.knowledge.knowledge_base import create_knowledge_base


KNOWLEDGE_GRAPH_VERSION = "1.0.0"


def build_knowledge_graph_from_discovery(discovery_report: dict[str, Any]) -> dict[str, Any]:
    """Build complete knowledge graph from Discovery report."""
    kb = create_knowledge_base()
    kb = register_discovery_hypotheses(kb, discovery_report)
    kb = store_discovery_insights(kb, discovery_report)

    graph = build_evidence_graph(kb)

    return {
        "success": True,
        "version": KNOWLEDGE_GRAPH_VERSION,
        "knowledge_base": kb,
        "evidence_graph": graph,
        "summary": build_knowledge_summary(kb, graph),
    }


def build_knowledge_summary(
    knowledge_base: dict[str, Any],
    graph: dict[str, Any],
) -> str:
    """Build human-readable knowledge summary."""
    return (
        f"Knowledge Graph contains {len(knowledge_base.get('hypotheses', {}))} hypothesis/hypotheses, "
        f"{len(knowledge_base.get('insights', {}))} insight(s), "
        f"{len(knowledge_base.get('evidence', {}))} evidence item(s), "
        f"and {graph.get('edge_count', 0)} relation(s)."
    )
