
"""Activate inference graph nodes from stimuli."""

from __future__ import annotations

from typing import Any


def activate_graph(
    inference_graph: dict[str, Any],
    stimuli: dict[str, float],
) -> dict[str, Any]:
    """Assign activation values to graph nodes."""
    nodes = inference_graph.get("nodes", [])
    activations = {}

    for node in nodes:
        label = node.get("label", "")
        base = float(node.get("confidence", 0.0)) * 0.35
        stimulus = float(stimuli.get(label, 0.0))
        activation = min(1.0, base + stimulus)
        activations[node.get("node_id", label)] = round(activation, 6)

    return {
        "node_activations": activations,
        "active_nodes": sorted(
            [
                {"node_id": node_id, "activation": value}
                for node_id, value in activations.items()
                if value >= 0.35
            ],
            key=lambda item: item["activation"],
            reverse=True,
        ),
    }
