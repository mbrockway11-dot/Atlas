"""Research matrix exporter.

The research matrix intentionally excludes legacy aggregate ranking fields
such as kamea_score.

Rows should contain observable structural features only. Kamea/cipher/planet
remain construction metadata, not scoring targets.
"""

from __future__ import annotations

from typing import Any

from atlas.research.attractor_metrics import build_layer_attractor_metrics
from atlas.research.coherence_metrics import build_layer_coherence_metrics
from atlas.research.graph_metrics import build_layer_graph_metrics
from atlas.research.reduction_metrics import build_layer_reduction_metrics


def build_research_matrix(names: list[str]) -> list[dict[str, Any]]:
    """Build one research row per person x cipher x planet."""
    from atlas.acf.builder import build_acf_profile

    rows = []

    for name in names:
        acf = build_acf_profile(name)
        rows.extend(build_profile_matrix_rows(acf))

    return rows


def build_profile_matrix_rows(acf: dict[str, Any]) -> list[dict[str, Any]]:
    """Build research matrix rows from one ACF profile."""
    rows = []
    identity = acf["identity"]["name"]
    persistence = acf["identity_persistence"]["summary"]

    for layer in acf["identity_graph"]["layers"]:
        features = layer["features"]
        path_views = features["path_views"]
        analysis_path = path_views["analysis_path"]
        visit_history = analysis_path["visit_history"]

        wrapped_values = analysis_path["wrapped_values"]
        node_weights = analysis_path["node_weights"]
        edge_weights = analysis_path["edge_weights"]

        grid_capacity = layer["grid_size"] * layer["grid_size"]
        unique_nodes = len(node_weights)
        unique_edges = len(edge_weights)

        graph_metrics = build_layer_graph_metrics(layer)
        coherence_metrics = build_layer_coherence_metrics(layer)
        reduction_metrics = build_layer_reduction_metrics(layer)
        attractor_metrics = build_layer_attractor_metrics(layer)

        rows.append(
            {
                "name": identity,
                "cipher": layer["cipher"],
                "planet": layer["planet"],
                "kamea": layer["kamea"],
                "grid_size": layer["grid_size"],
                "grid_capacity": grid_capacity,
                "sequence_length": len(wrapped_values),
                "unique_nodes": unique_nodes,
                "node_coverage": (
                    unique_nodes / grid_capacity
                    if grid_capacity
                    else 0.0
                ),
                "unique_edges": unique_edges,
                "max_node_weight": (
                    max(node_weights.values())
                    if node_weights
                    else 0
                ),
                "max_depth": visit_history["max_depth"],
                "self_loops": features["self_loops"],
                "density": features["density"],
                "clusters": features["clusters"],
                "entropy": features["entropy"],
                "axis_strength": features["axis_strength"],
                **graph_metrics,
                **coherence_metrics,
                **reduction_metrics,
                **attractor_metrics,
                "subtype_primary": layer["subtype"]["primary_type"],
                "subtype_secondary": layer["subtype"]["secondary_modifier"],
                "profile_node_persistence_ratio": persistence[
                    "node_persistence_ratio"
                ],
                "profile_edge_persistence_ratio": persistence[
                    "edge_persistence_ratio"
                ],
            }
        )

    return rows