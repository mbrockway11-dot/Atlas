
"""Propagate activation through inference graph edges."""

from __future__ import annotations

from typing import Any


def propagate_activation(
    inference_graph: dict[str, Any],
    node_activations: dict[str, float],
    *,
    decay: float = 0.72,
) -> dict[str, Any]:
    """Propagate activation one step through graph edges."""
    propagated = dict(node_activations)

    for edge in inference_graph.get("edges", []):
        source = edge.get("source")
        target = edge.get("target")

        if source not in node_activations:
            continue

        relation = edge.get("relation", "supports")
        weight = float(edge.get("weight", 0.5))
        signal = node_activations[source] * weight * decay

        if relation == "tension":
            signal *= -0.5

        propagated[target] = max(-1.0, min(1.0, propagated.get(target, 0.0) + signal))

    return {
        "propagated_activations": {
            key: round(value, 6)
            for key, value in propagated.items()
        },
        "top_activated": sorted(
            [
                {"node_id": key, "activation": round(value, 6)}
                for key, value in propagated.items()
            ],
            key=lambda item: item["activation"],
            reverse=True,
        )[:12],
    }
