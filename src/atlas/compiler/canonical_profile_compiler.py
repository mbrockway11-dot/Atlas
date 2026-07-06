"""Canonical Atlas profile compiler.

Single source of truth for profile compilation.

Input:
    profile.intake.json

Output:
    profile.payload.json

ACF is legacy/export only and should not be required by new services.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from atlas.semantic import build_semantic_profile
from atlas.knowledge.structural_synthesis import build_structural_synthesis
from atlas.synthesis import build_synthesis_report_from_payload
from atlas.systems_report import build_systems_engineering_report
from atlas.dynamics import build_unified_dynamics_report
from atlas.knowledge import build_knowledge_interpretation

from atlas.services.profile_path_service import resolve_profile_dir
from atlas.temporal.birth import build_birth_data_from_intake
from atlas.temporal.natal_chart import build_natal_chart_payload
from atlas.interpretation.profile_classifier import classify_profile
from atlas.graph.identity_stack import build_identity_graph_stack, identity_graph_stack_to_dict
from atlas.kamea import build_kamea_identity_graph


CANONICAL_PROFILE_COMPILER_VERSION = "1.0"


def compile_canonical_profile(profile_key: str, *, force: bool = False) -> dict[str, Any]:
    """Compile one profile into canonical profile.payload.json."""
    clean_key = profile_key.strip()

    if not clean_key:
        return failure_payload("", "profile_key is required.")

    profile_dir = resolve_profile_dir(clean_key)
    profile_dir.mkdir(parents=True, exist_ok=True)

    intake_path = profile_dir / "profile.intake.json"
    payload_path = profile_dir / "profile.payload.json"

    if payload_path.exists() and not force:
        return read_json(payload_path)

    if not intake_path.exists():
        return failure_payload(
            clean_key,
            f"Missing profile.intake.json: {intake_path}",
            profile_dir=profile_dir,
        )

    intake = read_json(intake_path)

    payload: dict[str, Any] = {
        "success": True,
        "version": CANONICAL_PROFILE_COMPILER_VERSION,
        "profile_key": clean_key,
        "profile_dir": str(profile_dir),
        "payload_path": str(payload_path),
        "identity": build_identity(clean_key, intake),
        "birth": build_birth(intake),
        "death": build_death(intake),
        "lifecycle": build_lifecycle(intake),
        "cipher": missing_layer("cipher", "Cipher compiler not wired into canonical compiler yet."),
        "kamea": {},
        "graph": {},
        "topology": {},
        "resonance": {},
        "fingerprint": {},
        "temporal": build_temporal(intake),
        "classification": {},
        "structural_synthesis": {},
        "synthesis": {},
        "systems_report": {},
        "narrative": missing_layer("narrative", "Narrative compiler not wired into canonical compiler yet."),
        "evidence": [],
        "metrics": {},
        "diagnostics": {
            "warnings": [],
            "errors": [],
            "created_at": now_utc(),
            "compiler": "canonical_profile_compiler",
        },
    }

    payload["kamea"] = build_kamea_layer(payload)

    graph_layers = build_graph_layers(payload)
    payload.update(graph_layers)

    payload["metrics"] = build_metrics(payload)
    payload["classification"] = classify_profile(payload)
    payload["metrics"] = build_metrics(payload)

    semantic = build_semantic_profile(payload)
    payload["semantic"] = semantic
    payload["metrics"]["has_semantic"] = bool(semantic.get("success"))

    structural_synthesis = build_structural_synthesis(payload)
    payload["structural_synthesis"] = structural_synthesis
    payload["metrics"]["has_structural_synthesis"] = bool(structural_synthesis.get("success"))

    synthesis = build_synthesis_report_from_payload(payload)
    payload["synthesis"] = synthesis
    payload["metrics"]["has_synthesis"] = bool(synthesis.get("success"))

    systems_report = build_systems_engineering_report(payload)
    payload["systems_report"] = systems_report

    dynamics_report = build_unified_dynamics_report(payload)
    payload["dynamics"] = dynamics_report
    payload["metrics"]["has_dynamics"] = bool(dynamics_report.get("success"))

    knowledge_interpretation = build_knowledge_interpretation(payload)
    payload["knowledge_interpretation"] = knowledge_interpretation
    payload["metrics"]["has_knowledge_interpretation"] = bool(knowledge_interpretation.get("success"))
    payload["metrics"]["has_systems_report"] = bool(systems_report.get("success"))

    write_json(payload_path, payload)

    return payload


def build_identity(profile_key: str, intake: dict[str, Any]) -> dict[str, Any]:
    """Build canonical identity block."""
    identity = intake.get("identity", {}) if isinstance(intake.get("identity"), dict) else {}

    name = (
        identity.get("display_name")
        or identity.get("full_name")
        or intake.get("name")
        or intake.get("full_name")
        or profile_key.replace("_", " ").title()
    )

    return {
        "profile_key": profile_key,
        "name": name,
        "display_name": name,
        "full_name": identity.get("full_name") or name,
    }


def build_birth(intake: dict[str, Any]) -> dict[str, Any]:
    """Build canonical birth block."""
    birth = intake.get("birth", {}) if isinstance(intake.get("birth"), dict) else {}

    return {
        "date": birth.get("date") or intake.get("birth_date", ""),
        "time": birth.get("time") or intake.get("birth_time", ""),
        "place": birth.get("place") or intake.get("birth_place", "") or intake.get("birth_location", ""),
        "date_status": birth.get("date_status", "missing"),
        "time_status": birth.get("time_status", "missing"),
        "place_status": birth.get("place_status", "missing"),
    }


def build_death(intake: dict[str, Any]) -> dict[str, Any]:
    """Build canonical death block."""
    death = intake.get("death", {}) if isinstance(intake.get("death"), dict) else {}

    return {
        "date": death.get("date") or intake.get("death_date", ""),
        "place": death.get("place") or intake.get("death_place", ""),
        "date_status": death.get("date_status", "open_or_missing"),
        "place_status": death.get("place_status", "missing"),
        "lifecycle_status": death.get("lifecycle_status", "open_lifecycle"),
    }


def build_lifecycle(intake: dict[str, Any]) -> dict[str, Any]:
    """Build lifecycle block from intake."""
    return {
        "status": "compiled",
        "major_events": intake.get("major_events", []),
        "notes": intake.get("notes", ""),
    }



def build_kamea_layer(payload: dict[str, Any]) -> dict[str, Any]:
    """Build canonical Kamea layer."""
    try:
        graph = build_kamea_identity_graph(payload)

        safe_graph = json_safe(graph)

        return {
            "status": "compiled",
            "version": safe_graph.get("version", "1.0"),
            "summary": safe_graph.get("summary", {}),
            "construction_passes": safe_graph.get("construction_passes", []),
            "nodes": safe_graph.get("nodes", {}),
            "edges": safe_graph.get("edges", {}),
            "metadata": safe_graph.get("metadata", {}),
            "raw_graph": safe_graph,
        }

    except Exception as exc:
        return missing_layer(
            "kamea",
            f"Kamea compilation failed: {exc}",
        )


def build_graph_layers(payload: dict[str, Any]) -> dict[str, Any]:
    """Build graph, topology, resonance, and fingerprint layers."""
    try:
        graph_input = build_graph_input(payload)
        stack = build_identity_graph_stack(graph_input)
        stack_data = identity_graph_stack_to_dict(stack)
        summary = stack_data.get("summary", {})

        return {
            "graph": {
                "status": "compiled",
                "identity_stack": stack_data,
                "summary": summary,
                "cig": stack_data.get("cig", {}),
                "stg": stack_data.get("stg", {}),
                "motifs": stack_data.get("motifs", {}),
                "genome": stack_data.get("genome", {}),
            },
            "topology": {
                "status": "compiled",
                "summary": stack_data.get("topology", {}).get("summary", {}),
                "topology_class": summary.get("topology_class", "n/a"),
                "dominant_topology_axis": summary.get("dominant_topology_axis", "n/a"),
                "dominant_motif": summary.get("dominant_motif", "n/a"),
                "motif_count": summary.get("motif_richness", 0),
            },
            "resonance": {
                "status": "compiled",
                "summary": stack_data.get("resonance", {}).get("summary", {}),
                "resonance_class": summary.get("resonance_class", "n/a"),
                "dominant_resonance_axis": summary.get("dominant_resonance_axis", "n/a"),
            },
            "fingerprint": {
                "status": "compiled",
                "summary": {
                    "cig_nodes": summary.get("raw_node_count", 0),
                    "cig_edges": summary.get("raw_edge_count", 0),
                    "stg_nodes": summary.get("truth_node_count", 0),
                    "stg_edges": summary.get("truth_edge_count", 0),
                    "dominant_motif": summary.get("dominant_motif", "n/a"),
                    "topology_class": summary.get("topology_class", "n/a"),
                    "resonance_class": summary.get("resonance_class", "n/a"),
                },
            },
        }

    except Exception as exc:
        reason = f"Graph compilation failed: {exc}"
        return {
            "graph": missing_layer("graph", reason),
            "topology": missing_layer("topology", reason),
            "resonance": missing_layer("resonance", reason),
            "fingerprint": missing_layer("fingerprint", reason),
        }


def build_graph_input(payload: dict[str, Any]) -> dict[str, Any]:
    """Build legacy-compatible graph input from Kamea identity graph."""
    identity = payload.get("identity", {})
    kamea_layer = payload.get("kamea", {})
    kamea_graph = kamea_layer.get("raw_graph") or kamea_layer
    layers = build_kamea_graph_layers(kamea_graph)

    return {
        "identity": {
            "name": identity.get("name") or identity.get("display_name") or payload.get("profile_key", ""),
            "profile_key": payload.get("profile_key", ""),
        },
        "identity_graph": {
            "version": "2.0-kamea",
            "source": "atlas.kamea.identity_graph",
            "layers": layers,
            "raw_kamea_graph": kamea_graph,
            "summary": kamea_graph.get("summary", {}),
        },
    }


def build_kamea_graph_layers(kamea_graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert native Kamea graph into graph-stack layer records."""
    layers: list[dict[str, Any]] = []
    nodes = kamea_graph.get("nodes", {})
    edges = kamea_graph.get("edges", {})

    for index, construction_pass in enumerate(kamea_graph.get("construction_passes", [])):
        cipher = construction_pass.get("cipher", "unknown_cipher")
        planet = construction_pass.get("planet", "unknown_planet")
        layer_id = f"kamea_layer_{index}_{cipher}_{planet}"

        layer_nodes = [
            {
                "id": node_id,
                "label": node.get("label", node_id),
                "type": node.get("type", "kamea_node"),
                "weight": node.get("weight", 1),
                "cipher_count": node.get("cipher_count", 1),
                "planet_count": node.get("planet_count", 1),
                "coordinate": node.get("coordinate"),
            }
            for node_id, node in nodes.items()
            if cipher in node.get("ciphers", []) and planet in node.get("planets", [])
        ]

        layer_node_ids = {node["id"] for node in layer_nodes}

        layer_edges = [
            {
                "source": edge.get("source"),
                "target": edge.get("target"),
                "type": edge.get("type", "kamea_path"),
                "weight": edge.get("weight", 1),
            }
            for edge in edges.values()
            if edge.get("cipher") == cipher
            and edge.get("planet") == planet
            and edge.get("source") in layer_node_ids
            and edge.get("target") in layer_node_ids
        ]

        path_views = construction_pass.get("path_views", {})
        if not isinstance(path_views, dict) or not path_views:
            path_views = build_minimal_path_views(
                node_id=layer_nodes[0]["id"] if layer_nodes else layer_id,
                previous_node=None,
                index=index,
            )

        layers.append(
            {
                "id": layer_id,
                "layer_id": layer_id,
                "cipher": cipher,
                "planet": planet,
                "features": {
                    "source": "kamea_identity_graph",
                    "cipher": cipher,
                    "planet": planet,
                    "path_views": path_views,
                    "value_count": construction_pass.get("value_count", 0),
                    "path_length": construction_pass.get("path_length", 0),
                    "repeated_nodes": construction_pass.get("repeated_nodes", {}),
                    "repeated_edges": construction_pass.get("repeated_edges", {}),
                },
                "label": f"{cipher} / {planet}",
                "nodes": layer_nodes,
                "edges": layer_edges,
            }
        )

    return layers


def build_minimal_path_views(
    *,
    node_id: str,
    previous_node: str | None,
    index: int,
) -> dict[str, Any]:
    """Build minimal path_views contract for graph stack."""
    sequence = [previous_node, node_id] if previous_node else [node_id]
    visits = [
        {
            "node": node,
            "coordinate": [position, 0],
            "depth": position,
            "visit_depth": position,
            "visit_index": position,
            "sequence_index": position,
        }
        for position, node in enumerate(sequence)
    ]

    node_weights = {node: sequence.count(node) for node in sequence}
    edge_weights = {}

    if previous_node:
        edge_weights[f"{previous_node}->{node_id}"] = 1

    return {
        "analysis_path": {
            "raw_values": sequence,
            "wrapped_values": sequence,
            "node_weights": node_weights,
            "edge_weights": edge_weights,
            "visit_history": {
                "visits": visits,
                "visit_count": len(visits),
            },
        },
        "render_path": {
            "wrapped_values": sequence,
            "coordinates": [
                [position, 0]
                for position, _node in enumerate(sequence)
            ],
        },
    }


def build_temporal(intake: dict[str, Any]) -> dict[str, Any]:
    """Build canonical temporal block."""
    try:
        birth = build_birth(intake)
        identity = intake.get("identity", {}) if isinstance(intake.get("identity"), dict) else {}

        temporal_intake = {
            **intake,
            "name": identity.get("display_name") or identity.get("full_name") or intake.get("profile_key", ""),
            "birth_date": birth.get("date", ""),
            "birth_time": birth.get("time", ""),
            "birth_place": birth.get("place", ""),
            "birth_location": birth.get("place", ""),
        }

        birth_data = build_birth_data_from_intake(temporal_intake)
        natal_payload = build_natal_chart_payload(birth_data)

        return {
            "status": "compiled",
            "birth": birth,
            "natal": {
                "ephemeris": natal_payload.get("ephemeris", {}),
                "sidereal": natal_payload.get("sidereal", {}),
            },
            "summary": natal_payload.get("ephemeris", {}).get("summary", {}),
            "warnings": natal_payload.get("warnings", []),
            "errors": natal_payload.get("errors", []),
        }

    except Exception as exc:
        return {
            "status": "missing",
            "reason": f"Temporal compilation failed: {exc}",
            "required_inputs": ["birth.date", "birth.time", "birth.place"],
            "warnings": [],
            "errors": [str(exc)],
        }


def build_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    """Build canonical profile metrics."""
    temporal = payload.get("temporal", {})
    topology = payload.get("topology", {})
    resonance = payload.get("resonance", {})
    classification = payload.get("classification", {})

    return {
        "has_identity": bool(payload.get("identity", {}).get("name")),
        "has_birth_date": bool(payload.get("birth", {}).get("date")),
        "has_birth_time": bool(payload.get("birth", {}).get("time")),
        "has_birth_location": bool(payload.get("birth", {}).get("place")),
        "has_temporal": temporal.get("status") == "compiled",
        "has_natal": bool(temporal.get("natal")),
        "has_ephemeris": bool(temporal.get("natal", {}).get("ephemeris")),
        "has_graph": payload.get("graph", {}).get("status") == "compiled",
        "has_topology": topology.get("status") == "compiled",
        "has_resonance": resonance.get("status") == "compiled",
        "has_fingerprint": payload.get("fingerprint", {}).get("status") == "compiled",
        "has_classification": bool(classification.get("structural_role")),
            "has_dynamics": bool(payload.get("dynamics", {}).get("success")),
}


def missing_layer(layer: str, reason: str) -> dict[str, Any]:
    """Return a stable missing-layer object."""
    return {
        "status": "missing",
        "layer": layer,
        "reason": reason,
        "required_inputs": [],
        "warnings": [],
        "errors": [],
    }


def failure_payload(
    profile_key: str,
    error: str,
    *,
    profile_dir: Path | None = None,
) -> dict[str, Any]:
    """Return failure payload."""
    return {
        "success": False,
        "version": CANONICAL_PROFILE_COMPILER_VERSION,
        "profile_key": profile_key,
        "profile_dir": str(profile_dir) if profile_dir else "",
        "payload_path": "",
        "warnings": [],
        "errors": [error],
    }


def read_json(path: Path) -> dict[str, Any]:
    """Read JSON artifact."""
    return json.loads(path.read_text(encoding="utf-8"))



def json_safe(value: Any) -> Any:
    """Convert nested structures to JSON-safe values."""
    if isinstance(value, dict):
        return {
            stringify_key(key): json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            json_safe(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            json_safe(item)
            for item in value
        ]

    return value


def stringify_key(key: Any) -> str:
    """Convert dict keys to JSON-safe strings."""
    if isinstance(key, tuple):
        return "|".join(str(item) for item in key)

    return str(key)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON artifact."""
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def now_utc() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()
