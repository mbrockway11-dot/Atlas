"""Atlas planetary consensus vectors."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean, pstdev
from typing import Any

from atlas.research.vectors import PRIMARY_METRICS


def build_planetary_vectors(
    layer_vectors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build one consensus vector for each planet from the
    three cipher-specific layer vectors.

    Returns
    -------
    Seven planetary vectors.
    """

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for layer in layer_vectors:
        grouped[layer["planet"]].append(layer)

    output = []

    for planet in sorted(grouped):

        layers = grouped[planet]

        metrics = {}

        for metric in PRIMARY_METRICS:

            values = [
                layer["vector"][metric]
                for layer in layers
            ]

            metrics[metric] = {
                "mean": mean(values),
                "std": pstdev(values) if len(values) > 1 else 0.0,
                "minimum": min(values),
                "maximum": max(values),
                "range": max(values) - min(values),
            }

        output.append(
            {
                "name": layers[0]["name"],
                "planet": planet,
                "layer_count": len(layers),
                "cipher_vectors": layers,
                "consensus": metrics,
                "consensus_strength": calculate_consensus_strength(metrics),
            }
        )

    return output


def calculate_consensus_strength(
    metrics: dict[str, Any],
) -> float:
    """
    Consensus ranges from 0–1.

    1.0 means all three ciphers agree perfectly.

    Larger standard deviations reduce confidence.
    """

    spreads = [
        metric["std"]
        for metric in metrics.values()
    ]

    average_spread = mean(spreads)

    return max(
        0.0,
        1.0 - average_spread,
    )