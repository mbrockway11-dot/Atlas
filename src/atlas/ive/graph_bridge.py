"""Graph Intelligence bridge for Identity Vector Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas.fingerprint import StructuralFingerprint
from atlas.graph.activation import GraphActivation
from atlas.graph.metrics import GraphMetrics
from atlas.graph.propagation import PropagationResult
from atlas.ive.schema import IVE_VERSION


IVE_GRAPH_BRIDGE_VERSION = "0.1"


@dataclass(frozen=True)
class GraphBackedIdentityVector:
    """Graph-backed IVE integration payload.

    This does not replace the legacy ACF-backed IdentityVector.
    It provides a bridge from Atlas graph intelligence into IVE-compatible
    global features, diagnostics, quality metadata, and vector exports.
    """

    version: str
    profile_key: str
    global_features: dict[str, float]
    diagnostics: dict[str, Any]
    quality: dict[str, Any]
    source_fingerprint: dict[str, Any]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe graph-backed IVE payload."""
        return {
            "version": self.version,
            "profile_key": self.profile_key,
            "global_features": self.global_features,
            "diagnostics": self.diagnostics,
            "quality": self.quality,
            "source_fingerprint": self.source_fingerprint,
            "metadata": self.metadata,
        }


def build_graph_backed_identity_vector(
    *,
    profile_key: str,
    metrics: GraphMetrics,
    activation: GraphActivation,
    propagation: PropagationResult,
    fingerprint: StructuralFingerprint,
) -> GraphBackedIdentityVector:
    """Build IVE-compatible vector from graph intelligence outputs."""
    global_features = build_graph_ive_global_features(
        metrics=metrics,
        activation=activation,
        propagation=propagation,
        fingerprint=fingerprint,
    )

    diagnostics = {
        "activation_center": activation.summary.get("activation_center"),
        "propagation_top_node": propagation.summary.get("top_node"),
        "hub_count": len(metrics.hub_nodes),
        "isolated_node_count": len(metrics.isolated_nodes),
        "top_nodes": list(propagation.top_nodes),
        "structural_hash": fingerprint.structural_hash,
    }

    quality = {
        "source": "graph_intelligence",
        "ive_bridge_version": IVE_GRAPH_BRIDGE_VERSION,
        "fingerprint_type": fingerprint.metadata.get("fingerprint_type"),
        "has_structural_hash": bool(fingerprint.structural_hash),
        "feature_count": len(global_features),
        "legacy_acf_vector": False,
    }

    return GraphBackedIdentityVector(
        version=IVE_VERSION,
        profile_key=profile_key,
        global_features=global_features,
        diagnostics=diagnostics,
        quality=quality,
        source_fingerprint=fingerprint.to_dict(),
        metadata={
            "bridge": "atlas.ive.graph_bridge",
            "bridge_version": IVE_GRAPH_BRIDGE_VERSION,
            "status": "integrated",
        },
    )


def build_graph_ive_global_features(
    *,
    metrics: GraphMetrics,
    activation: GraphActivation,
    propagation: PropagationResult,
    fingerprint: StructuralFingerprint,
) -> dict[str, float]:
    """Build normalized IVE-style global features from graph intelligence."""
    vector = fingerprint.vector

    node_count = max(float(vector.get("node_count", metrics.node_count)), 1.0)
    edge_count = max(float(vector.get("edge_count", metrics.edge_count)), 1.0)

    activation_density = _safe_ratio(
        float(activation.summary.get("activated_node_count", 0.0)),
        node_count,
    )
    edge_activation_density = _safe_ratio(
        float(activation.summary.get("activated_edge_count", 0.0)),
        edge_count,
    )

    graph_density = _clamp(float(metrics.density))
    average_degree = _clamp(float(metrics.average_degree) / max(node_count, 1.0))
    max_degree = _clamp(float(metrics.max_degree) / max(node_count, 1.0))

    propagation_total = _clamp(
        float(propagation.summary.get("total_score", 0.0))
        / max(node_count, 1.0)
    )
    propagation_max = _clamp(float(propagation.summary.get("max_score", 0.0)))

    isolation_ratio = _safe_ratio(len(metrics.isolated_nodes), node_count)
    hub_ratio = _safe_ratio(len(metrics.hub_nodes), node_count)

    structural_complexity = _clamp(
        (
            graph_density
            + average_degree
            + activation_density
            + edge_activation_density
        )
        / 4.0
    )

    structural_stability = _clamp(
        (
            propagation_max
            + propagation_total
            + (1.0 - isolation_ratio)
        )
        / 3.0
    )

    identity_balance = _clamp(
        1.0
        - abs(hub_ratio - isolation_ratio)
    )

    return {
        "graph_density_index": graph_density,
        "average_degree_index": average_degree,
        "max_degree_index": max_degree,
        "activation_density_index": activation_density,
        "edge_activation_density_index": edge_activation_density,
        "propagation_total_index": propagation_total,
        "propagation_max_index": propagation_max,
        "hub_ratio": _clamp(hub_ratio),
        "isolation_ratio": _clamp(isolation_ratio),
        "structural_complexity_index": structural_complexity,
        "structural_stability_index": structural_stability,
        "planet_balance_index": identity_balance,
    }


def graph_backed_identity_vector_to_dict(
    vector: GraphBackedIdentityVector,
) -> dict[str, Any]:
    """Convert graph-backed IVE vector to dictionary."""
    return vector.to_dict()


def _safe_ratio(
    numerator: float,
    denominator: float,
) -> float:
    """Return safe clamped ratio."""
    if denominator <= 0:
        return 0.0

    return _clamp(numerator / denominator)


def _clamp(value: float) -> float:
    """Clamp value to 0-1."""
    return max(0.0, min(1.0, float(value)))
