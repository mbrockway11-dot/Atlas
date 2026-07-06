
"""Service layer for Systems Engineering Report dashboard."""

from __future__ import annotations

from typing import Any

from atlas.compiler.canonical_profile_compiler import compile_canonical_profile
from atlas.library.profile_library import list_saved_profiles
from atlas.systems_report import build_systems_engineering_report


def list_systems_report_profiles() -> list[str]:
    """List available profiles for Systems Engineering Report."""
    return list_saved_profiles()


def build_systems_report_payload(profile_key: str, *, force: bool = False) -> dict[str, Any]:
    """Build Systems Engineering Report payload."""
    payload = compile_canonical_profile(profile_key, force=force)

    if not payload.get("success"):
        return {
            "success": False,
            "profile_key": profile_key,
            "errors": payload.get("errors", []),
            "payload": payload,
            "report": {},
        }

    report = payload.get("systems_report") or build_systems_engineering_report(payload)

    return {
        "success": True,
        "profile_key": profile_key,
        "errors": [],
        "payload": payload,
        "report": report,
    }



def build_interactive_structural_graph(report: dict[str, Any]) -> dict[str, Any]:
    """Build dashboard-safe structural graph payload."""
    graph = report.get("diagrams", {}).get("inference_graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    return {
        "success": True,
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "dot": build_graphviz_dot(nodes, edges),
    }


def build_graphviz_dot(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> str:
    """Build Graphviz DOT for inference graph."""
    lines = [
        "digraph AtlasStructuralGraph {",
        "rankdir=LR;",
        "node [shape=box, style=rounded, fontsize=10];",
        "edge [fontsize=9];",
    ]

    for node in nodes:
        node_id = safe_dot_id(node.get("node_id", "unknown"))
        label = node.get("label", node_id)
        node_type = node.get("node_type", "node")
        confidence = node.get("confidence", 0)

        shape = "box"
        if node_type == "inference":
            shape = "oval"

        lines.append(
            f'{node_id} [label="{escape_dot(label)}\\n{node_type}\\n{confidence}", shape={shape}];'
        )

    for edge in edges:
        source = safe_dot_id(edge.get("source", "unknown_source"))
        target = safe_dot_id(edge.get("target", "unknown_target"))
        relation = edge.get("relation", "")
        weight = edge.get("weight", "")

        lines.append(
            f'{source} -> {target} [label="{escape_dot(relation)} {weight}"];'
        )

    lines.append("}")
    return "\n".join(lines)


def safe_dot_id(value: Any) -> str:
    """Convert node id to safe Graphviz identifier."""
    text = str(value)
    return "n_" + "".join(char if char.isalnum() else "_" for char in text)


def escape_dot(value: Any) -> str:
    """Escape label value for DOT."""
    return str(value).replace('"', "'").replace("\\", "/")
