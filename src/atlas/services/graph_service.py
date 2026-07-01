"""Graph service layer for Identity Stack and Morphology dashboards."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.graph.identity_morphology import (
    compare_identity_morphology,
    identity_morphology_to_dict,
)
from atlas.graph.identity_stack import (
    build_identity_graph_stack,
    identity_graph_stack_to_dict,
)
from atlas.graph.stack_audit import audit_identity_stack, stack_audit_to_dict
from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles
from atlas.visualization import build_canonical_graph_figure


def list_graph_profiles() -> list[str]:
    """Return available graph profile keys."""
    return list_saved_profiles()


def load_graph_acf(profile_key: str) -> dict[str, Any] | None:
    """Load an ACF profile safely."""
    acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

    if not acf_path.exists():
        return None

    return json.loads(acf_path.read_text(encoding="utf-8"))


def build_identity_stack_payload(profile_key: str) -> dict[str, Any]:
    """Build identity graph stack, audit, and export payload."""
    acf = load_graph_acf(profile_key)

    if acf is None:
        return {
            "success": False,
            "profile_key": profile_key,
            "errors": [f"Missing profile.acf.json for {profile_key}"],
            "warnings": [],
            "data": {},
            "exports": {},
            "metrics": {},
        }

    stack = build_identity_graph_stack(acf)
    stack_data = identity_graph_stack_to_dict(stack)

    audit = audit_identity_stack(stack_data)
    audit_data = stack_audit_to_dict(audit)

    return {
        "success": True,
        "profile_key": profile_key,
        "errors": [],
        "warnings": [],
        "data": {
            "acf": acf,
            "stack": stack,
            "stack_data": stack_data,
            "audit": audit,
            "audit_data": audit_data,
        },
        "exports": {
            "full_stack": stack_data,
            "summary": stack_data.get("summary", {}),
            "compact": build_compact_stack_export(stack_data),
            "audit": audit_data,
        },
        "metrics": build_identity_stack_metrics(stack_data, audit_data),
    }


def build_morphology_payload(
    profile_a: str,
    profile_b: str,
) -> dict[str, Any]:
    """Build graph morphology comparison payload."""
    acf_a = load_graph_acf(profile_a)
    acf_b = load_graph_acf(profile_b)

    errors: list[str] = []

    if acf_a is None:
        errors.append(f"Missing profile.acf.json for {profile_a}")

    if acf_b is None:
        errors.append(f"Missing profile.acf.json for {profile_b}")

    if errors:
        return {
            "success": False,
            "profile_a": profile_a,
            "profile_b": profile_b,
            "errors": errors,
            "warnings": [],
            "data": {},
            "exports": {},
            "metrics": {},
        }

    stack_a = build_identity_graph_stack(acf_a)
    stack_b = build_identity_graph_stack(acf_b)

    morphology = compare_identity_morphology(stack_a, stack_b)
    morphology_data = identity_morphology_to_dict(morphology)

    return {
        "success": True,
        "profile_a": profile_a,
        "profile_b": profile_b,
        "errors": [],
        "warnings": [],
        "data": {
            "acf_a": acf_a,
            "acf_b": acf_b,
            "stack_a": stack_a,
            "stack_b": stack_b,
            "morphology": morphology,
            "morphology_data": morphology_data,
        },
        "exports": {
            "morphology": morphology_data,
        },
        "metrics": build_morphology_metrics(morphology_data),
    }


def build_graph_figure(
    graph: dict[str, Any],
    *,
    title: str,
    layout: str,
) -> Any:
    """Build canonical graph visualization figure."""
    return build_canonical_graph_figure(
        graph,
        title=title,
        layout=layout,
    )


def get_cig_graph(stack_data: dict[str, Any]) -> dict[str, Any]:
    """Extract Canonical Identity Graph data."""
    return (
        stack_data.get("cig", {})
        .get("structural_attractor", {})
        .get("graph", {})
    )


def get_stg_graph(stack_data: dict[str, Any]) -> dict[str, Any]:
    """Extract Structural Truth Graph data."""
    return {
        "nodes": stack_data.get("stg", {}).get("nodes", {}),
        "edges": stack_data.get("stg", {}).get("edges", {}),
    }


def has_graph_data(graph: dict[str, Any]) -> bool:
    """Return whether graph has nodes and edges."""
    return bool(graph.get("nodes")) and bool(graph.get("edges"))


def build_compact_stack_export(stack_data: dict[str, Any]) -> dict[str, Any]:
    """Build compact identity stack export."""
    return {
        "version": stack_data.get("version"),
        "name": stack_data.get("name"),
        "summary": stack_data.get("summary", {}),
        "cig_summary": stack_data.get("cig", {}).get("summary", {}),
        "stg_summary": stack_data.get("stg", {}).get("summary", {}),
        "motif_summary": stack_data.get("motifs", {}).get("summary", {}),
        "genome_summary": stack_data.get("genome", {}).get("summary", {}),
        "topology_summary": stack_data.get("topology", {}).get("summary", {}),
        "resonance_summary": stack_data.get("resonance", {}).get("summary", {}),
    }


def build_identity_stack_metrics(
    stack_data: dict[str, Any],
    audit_data: dict[str, Any],
) -> dict[str, Any]:
    """Build identity stack summary metrics."""
    summary = stack_data.get("summary", {})

    return {
        "name": stack_data.get("name", "n/a"),
        "version": stack_data.get("version", "n/a"),
        "cig_nodes": summary.get("cig_node_count", 0),
        "cig_edges": summary.get("cig_edge_count", 0),
        "stg_nodes": summary.get("stg_node_count", 0),
        "stg_edges": summary.get("stg_edge_count", 0),
        "motif_count": summary.get("motif_count", 0),
        "audit_status": audit_data.get("status", "unknown"),
        "audit_errors": len(audit_data.get("errors", [])),
        "audit_warnings": len(audit_data.get("warnings", [])),
    }


def build_morphology_metrics(data: dict[str, Any]) -> dict[str, Any]:
    """Build morphology summary metrics."""
    return {
        "source": data.get("source_name", "n/a"),
        "target": data.get("target_name", "n/a"),
        "morphology_class": data.get("morphology_class", "n/a"),
        "distance": data.get("distance", 0),
        "similarity": data.get("similarity", 0),
        "mutation_score": data.get("mutation_score", 0),
    }


def json_export(data: Any) -> str:
    """Serialize JSON for download."""
    return json.dumps(data, indent=2, sort_keys=True)


def safe_filename(name: str) -> str:
    """Build safe filename slug."""
    safe = "".join(
        character.lower() if character.isalnum() else "_"
        for character in name
    ).strip("_")

    while "__" in safe:
        safe = safe.replace("__", "_")

    return safe or "graph_export"