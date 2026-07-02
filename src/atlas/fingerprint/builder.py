"""Identity fingerprint builder.

This module assembles the completed individual Atlas pipeline.

The fingerprint is not a population object. It is the canonical individual
identity model derived from a single IdentityGraph.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from atlas.acf.builder import build_acf_profile
from atlas.graph.analysis import analyze_identity_graph
from atlas.graph.attractor import extract_structural_attractor
from atlas.graph.coherence import compute_coherence_field
from atlas.graph.identity_graph import build_identity_graph_v2
from atlas.graph.reduction import reduce_identity_graph
from atlas.motifs.identity import detect_identity_graph_motifs


@dataclass(frozen=True)
class IdentityFingerprint:
    """Canonical individual identity fingerprint."""

    raw_identity_graph: dict[str, Any]
    analyzed_identity_graph: dict[str, Any]
    coherence_field: dict[str, Any]
    reduced_identity_graph: dict[str, Any]
    motifs: dict[str, Any]
    structural_attractor: dict[str, Any]
    classification: dict[str, Any]
    source_acf: Mapping[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        """Return the fingerprint as a plain dictionary."""
        return {
            "raw_identity_graph": self.raw_identity_graph,
            "analyzed_identity_graph": self.analyzed_identity_graph,
            "coherence_field": self.coherence_field,
            "reduced_identity_graph": self.reduced_identity_graph,
            "motifs": self.motifs,
            "structural_attractor": self.structural_attractor,
            "classification": self.classification,
            "source_acf": self.source_acf,
        }

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access for compatibility."""
        return self.to_dict()[key]

    def __contains__(self, key: str) -> bool:
        """Allow ``key in fingerprint`` for compatibility."""
        return key in self.to_dict()


class FunctionEngine:
    """Small adapter that exposes a function as an object method."""

    def __init__(self, function: Any, method_name: str) -> None:
        self.function = function
        self.method_name = method_name

    def __getattr__(self, name: str) -> Any:
        if name == self.method_name:
            return self.function

        raise AttributeError(name)


def build_identity_fingerprint(
    identity: str | None = None,
    *,
    identity_graph: dict[str, Any] | None = None,
    source_acf: Mapping[str, Any] | None = None,
    graph_analyzer: Any | None = None,
    coherence_engine: Any | None = None,
    reduction_engine: Any | None = None,
    motif_detector: Any | None = None,
    attractor_engine: Any | None = None,
    classification_engine: Any | None = None,
) -> IdentityFingerprint:
    """Build the full individual identity fingerprint."""
    resolved_acf = source_acf
    resolved_graph = identity_graph

    if resolved_graph is None:
        if resolved_acf is None:
            if identity is None:
                raise ValueError(
                    "build_identity_fingerprint requires either identity, "
                    "source_acf, or identity_graph."
                )

            resolved_acf = build_acf_profile(identity)

        resolved_graph = build_identity_graph_v2(dict(resolved_acf))

    graph_analyzer = graph_analyzer or FunctionEngine(
        analyze_identity_graph,
        "analyze",
    )
    coherence_engine = coherence_engine or FunctionEngine(
        compute_coherence_field,
        "compute",
    )
    reduction_engine = reduction_engine or FunctionEngine(
        reduce_identity_graph,
        "reduce",
    )
    motif_detector = motif_detector or FunctionEngine(
        detect_identity_graph_motifs,
        "detect",
    )
    attractor_engine = attractor_engine or FunctionEngine(
        extract_structural_attractor,
        "extract",
    )
    classification_engine = classification_engine or FunctionEngine(
        classify_individual_fingerprint,
        "classify",
    )

    raw_identity_graph = resolved_graph
    analyzed_identity_graph = graph_analyzer.analyze(raw_identity_graph)
    coherence_field = coherence_engine.compute(analyzed_identity_graph)
    reduced_identity_graph = reduction_engine.reduce(coherence_field)
    motifs = motif_detector.detect(reduced_identity_graph)

    structural_attractor = attractor_engine.extract(
        reduced_identity_graph,
        coherence_field=coherence_field,
        motifs=motifs,
    )

    classification = classification_engine.classify(
        raw_identity_graph=raw_identity_graph,
        analyzed_identity_graph=analyzed_identity_graph,
        coherence_field=coherence_field,
        reduced_identity_graph=reduced_identity_graph,
        motifs=motifs,
        structural_attractor=structural_attractor,
    )

    return IdentityFingerprint(
        raw_identity_graph=raw_identity_graph,
        analyzed_identity_graph=analyzed_identity_graph,
        coherence_field=coherence_field,
        reduced_identity_graph=reduced_identity_graph,
        motifs=motifs,
        structural_attractor=structural_attractor,
        classification=classification,
        source_acf=resolved_acf,
    )


def build_fingerprint_dict(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility helper returning a plain dictionary fingerprint."""
    return build_identity_fingerprint(*args, **kwargs).to_dict()


def classify_individual_fingerprint(
    *,
    raw_identity_graph: dict[str, Any],
    analyzed_identity_graph: dict[str, Any],
    coherence_field: dict[str, Any],
    reduced_identity_graph: dict[str, Any],
    motifs: dict[str, Any],
    structural_attractor: dict[str, Any],
) -> dict[str, Any]:
    """Classify one individual fingerprint from IdentityGraph v2 metrics."""
    attractor_summary = structural_attractor.get("summary", {})
    coherence_summary = coherence_field.get("coherence", {})
    motif_summary = motifs.get("summary", {})

    mean_node_coherence = attractor_summary.get("mean_node_coherence", 0.0)
    density = attractor_summary.get("density", 0.0)
    bridge_count = attractor_summary.get("bridge_count", 0)
    articulation_count = attractor_summary.get("articulation_point_count", 0)
    hub_count = attractor_summary.get("hub_count", 0)
    leaf_count = attractor_summary.get("leaf_count", 0)
    node_retention = attractor_summary.get("node_retention_ratio", 0.0)

    if mean_node_coherence >= 0.70 and density >= 0.35:
        structural_state = "coherent_core"
    elif bridge_count or articulation_count:
        structural_state = "bridge_mediated"
    elif leaf_count > hub_count:
        structural_state = "peripheral_branching"
    else:
        structural_state = "adaptive_field"

    if hub_count > 0 and bridge_count > 0:
        functional_role = "hub_bridge"
    elif hub_count > 0:
        functional_role = "hub"
    elif bridge_count > 0 or articulation_count > 0:
        functional_role = "bridge"
    elif density >= 0.45:
        functional_role = "mesh"
    else:
        functional_role = "chain_field"

    if node_retention >= 0.75:
        reduction_profile = "stable_dense_survivor"
    elif node_retention >= 0.40:
        reduction_profile = "selective_survivor"
    else:
        reduction_profile = "highly_reduced_core"

    return {
        "version": "2.0",
        "scale": "Individual",
        "population_free": True,
        "structural_state": structural_state,
        "functional_role": functional_role,
        "reduction_profile": reduction_profile,
        "drivers": {
            "mean_node_coherence": mean_node_coherence,
            "mean_edge_coherence": attractor_summary.get(
                "mean_edge_coherence",
                0.0,
            ),
            "density": density,
            "bridge_count": bridge_count,
            "articulation_point_count": articulation_count,
            "hub_count": hub_count,
            "leaf_count": leaf_count,
            "node_retention_ratio": node_retention,
            "edge_retention_ratio": attractor_summary.get(
                "edge_retention_ratio",
                0.0,
            ),
            "core_node_count": coherence_summary.get("core_node_count", 0),
            "core_edge_count": coherence_summary.get("core_edge_count", 0),
            "dominant_motif": motif_summary.get("dominant_motif", "none"),
            "total_motifs": motif_summary.get("total_motifs", 0),
            "raw_node_count": len(raw_identity_graph.get("nodes", {})),
            "analyzed_node_count": len(analyzed_identity_graph.get("nodes", {})),
            "reduced_node_count": len(reduced_identity_graph.get("nodes", {})),
        },
        "summary": (
            f"{functional_role} / {structural_state} / "
            f"{reduction_profile} / Individual"
        ),
    }
from hashlib import sha256

from atlas.graph.activation import GraphActivation
from atlas.graph.metrics import GraphMetrics
from atlas.graph.propagation import PropagationResult
from atlas.graph.resonance import GraphResonance


@dataclass(frozen=True)
class StructuralFingerprint:
    """Canonical structural fingerprint from graph intelligence outputs."""

    version: str
    profile_key: str
    vector: dict[str, float]
    labels: dict[str, Any]
    structural_hash: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe structural fingerprint."""
        return {
            "version": self.version,
            "profile_key": self.profile_key,
            "vector": self.vector,
            "labels": self.labels,
            "structural_hash": self.structural_hash,
            "metadata": self.metadata,
        }


def build_structural_fingerprint(
    *,
    profile_key: str,
    metrics: GraphMetrics,
    activation: GraphActivation,
    propagation: PropagationResult,
    resonance: GraphResonance | None = None,
) -> StructuralFingerprint:
    """Build deterministic structural fingerprint from graph intelligence."""
    vector = {
        "node_count": float(metrics.node_count),
        "edge_count": float(metrics.edge_count),
        "density": float(metrics.density),
        "average_degree": float(metrics.average_degree),
        "max_degree": float(metrics.max_degree),
        "activated_node_count": float(
            activation.summary.get("activated_node_count", 0)
        ),
        "activated_edge_count": float(
            activation.summary.get("activated_edge_count", 0)
        ),
        "max_node_activation": float(
            activation.summary.get("max_node_activation", 0.0)
        ),
        "total_node_activation": float(
            activation.summary.get("total_node_activation", 0.0)
        ),
        "total_edge_activation": float(
            activation.summary.get("total_edge_activation", 0.0)
        ),
        "propagation_max_score": float(
            propagation.summary.get("max_score", 0.0)
        ),
        "propagation_total_score": float(
            propagation.summary.get("total_score", 0.0)
        ),
    }

    if resonance is not None:
        vector.update(
            {
                "resonance_overall_score": float(resonance.overall_score),
                "resonance_node_overlap": float(resonance.node_overlap),
                "resonance_activation_overlap": float(
                    resonance.activation_overlap
                ),
            }
        )

    labels = {
        "activation_center": activation.summary.get("activation_center"),
        "propagation_top_node": propagation.summary.get("top_node"),
        "hub_nodes": list(metrics.hub_nodes),
        "isolated_nodes": list(metrics.isolated_nodes),
        "top_nodes": list(propagation.top_nodes),
    }

    structural_hash = _structural_hash(
        profile_key=profile_key,
        vector=vector,
        labels=labels,
    )

    return StructuralFingerprint(
        version="0.1",
        profile_key=profile_key,
        vector=vector,
        labels=labels,
        structural_hash=structural_hash,
        metadata={
            "fingerprint_type": "structural_graph",
            "source": "atlas.graph",
            "has_resonance": resonance is not None,
        },
    )


def _structural_hash(
    *,
    profile_key: str,
    vector: dict[str, float],
    labels: dict[str, Any],
) -> str:
    """Build deterministic structural hash."""
    parts = [profile_key]

    for key in sorted(vector):
        parts.append(f"{key}={vector[key]:.8f}")

    for key in sorted(labels):
        parts.append(f"{key}={labels[key]}")

    return sha256("|".join(parts).encode("utf-8")).hexdigest()
