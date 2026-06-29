"""Measurement explanations."""

from __future__ import annotations


METRIC_EXPLANATIONS = {
    "planet_balance_index": "How evenly structural emphasis is distributed across the seven planetary vectors.",
    "planet_variance_index": "How much the planetary vectors diverge from one another.",
    "structural_complexity_index": "How much complexity, entropy, coverage, articulation, and bridging appear in the identity vector.",
    "structural_stability_index": "How strongly the identity vector preserves coherent structure through reduction, topology, and attractor behavior.",
    "graph_coherence": "How consistently the graph reinforces organized structure instead of scattering across disconnected motion.",
    "entropy": "How evenly activity is distributed across active nodes.",
    "node_coverage": "How much of the available Kamea space is activated by the path.",
    "edge_coverage": "How much of the possible transition space is activated by the path.",
    "topology_stability": "How much of the graph's structure survives reduction.",
    "attractor_stability": "How stable the repeated attractor pattern is within the topology.",
    "bridge_ratio": "How much the structure depends on connector transitions between regions.",
    "loop_ratio": "How much the path reinforces repeated self-returning motion.",
    "hub_ratio": "How much activity concentrates through highly connected nodes.",
    "leaf_ratio": "How much of the topology terminates in weakly connected endpoints.",
    "reduction_entropy": "How much information remains distributed through the structure after reduction.",
}


def explain_metric(metric: str) -> str:
    """Return a plain-language explanation for a metric."""
    return METRIC_EXPLANATIONS.get(
        metric,
        "No explanation has been defined for this metric yet.",
    )


def explain_metric_value(metric: str, value: float) -> str:
    """Explain a metric value using low/medium/high bands."""
    band = classify_value(value)
    explanation = explain_metric(metric)

    return f"{metric}: {band}. {explanation}"


def classify_value(value: float) -> str:
    """Classify a bounded 0-1 value."""
    if value >= 0.75:
        return "high"
    if value >= 0.45:
        return "moderate"
    return "low"