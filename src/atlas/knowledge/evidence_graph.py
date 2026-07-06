
"""Evidence Graph.

Builds graph representation of hypotheses, insights, evidence, and relations.
"""

from __future__ import annotations

from typing import Any


EVIDENCE_GRAPH_VERSION = "1.0.0"


def build_evidence_graph(knowledge_base: dict[str, Any]) -> dict[str, Any]:
    """Build evidence graph from knowledge base."""
    nodes = []
    edges = []

    for hypothesis_id, hypothesis in (knowledge_base.get("hypotheses", {}) or {}).items():
        nodes.append(
            {
                "node_id": hypothesis_id,
                "node_type": "hypothesis",
                "label": hypothesis.get("hypothesis", hypothesis_id),
                "confidence": hypothesis.get("confidence", 0.0),
            }
        )

    for insight_id, insight in (knowledge_base.get("insights", {}) or {}).items():
        nodes.append(
            {
                "node_id": insight_id,
                "node_type": "insight",
                "label": insight.get("summary", insight.get("insight", insight_id)),
                "confidence": insight.get("confidence", 0.0),
            }
        )

    for evidence_id, evidence in (knowledge_base.get("evidence", {}) or {}).items():
        nodes.append(
            {
                "node_id": evidence_id,
                "node_type": "evidence",
                "label": evidence.get("source", evidence_id),
                "confidence": evidence.get("confidence", evidence.get("correlation", 0.0)),
            }
        )

    for relation in knowledge_base.get("relations", []) or []:
        edges.append(
            {
                "source": relation.get("source"),
                "target": relation.get("target"),
                "relation": relation.get("relation"),
                "weight": relation.get("weight", 1.0),
                "metadata": relation.get("metadata", {}),
            }
        )

    return {
        "success": True,
        "version": EVIDENCE_GRAPH_VERSION,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "summary": build_graph_summary(nodes, edges),
    }


def build_graph_summary(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    """Build evidence graph summary."""
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "hypothesis_count": sum(1 for node in nodes if node.get("node_type") == "hypothesis"),
        "insight_count": sum(1 for node in nodes if node.get("node_type") == "insight"),
        "evidence_count": sum(1 for node in nodes if node.get("node_type") == "evidence"),
    }
