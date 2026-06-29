"""Invariant structural subtype classification."""

from dataclasses import dataclass
from typing import Any

from atlas.invariant.features import InvariantFeatures


@dataclass(frozen=True)
class InvariantSubtype:
    """Invariant structural subtype result."""

    primary_type: str
    secondary_modifier: str
    scores: dict[str, float]


def classify_invariant_subtype(features: InvariantFeatures) -> InvariantSubtype:
    """Classify invariant features into structural subtype."""
    scores = score_invariant_subtypes(features)

    ranked = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    primary_type = ranked[0][0]
    secondary_modifier = ranked[1][0]

    return InvariantSubtype(
        primary_type=primary_type,
        secondary_modifier=secondary_modifier,
        scores=scores,
    )


def score_invariant_subtypes(features: InvariantFeatures) -> dict[str, float]:
    """Score all invariant subtypes."""
    loop_score = _clamp(features.self_loops / 3.0)
    low_entropy = 1.0 - features.entropy
    high_entropy = features.entropy
    clustering = _clamp(_cluster_cohesion(features))
    low_clustering = 1.0 - clustering
    fragmentation = _clamp((features.clusters - 1) / 3.0)
    balance = _balance_score(features)
    spread = _spread_score(features)
    branching = _branching_score(features)

    return {
        "Axial": _clamp(features.axis_strength),
        "Compressive": _clamp((loop_score + low_entropy) / 2.0),
        "Expansive": _clamp((high_entropy + spread) / 2.0),
        "Diffuse": _clamp(low_clustering),
        "Fragmented": fragmentation,
        "Balanced": balance,
        "Directive": _clamp((features.axis_strength + low_entropy) / 2.0),
        "Radial": _clamp((features.axis_strength + branching) / 2.0),
    }


def invariant_subtype_to_dict(subtype: InvariantSubtype) -> dict[str, Any]:
    """Convert subtype result to JSON-safe dictionary."""
    ranked = sorted(
        subtype.scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return {
        "primary_type": subtype.primary_type,
        "secondary_modifier": subtype.secondary_modifier,
        "scores": subtype.scores,
        "ranked": [
            {
                "type": item[0],
                "score": item[1],
            }
            for item in ranked
        ],
    }


def _cluster_cohesion(features: InvariantFeatures) -> float:
    """Estimate cohesion from density and cluster count."""
    if features.clusters <= 0:
        return 0.0

    cluster_penalty = 1.0 / features.clusters

    return _clamp((features.density + cluster_penalty) / 2.0)


def _balance_score(features: InvariantFeatures) -> float:
    """Score even distribution."""
    if not features.node_weights:
        return 0.0

    weights = list(features.node_weights.values())
    mean_weight = sum(weights) / len(weights)

    if mean_weight == 0:
        return 0.0

    avg_deviation = sum(
        abs(weight - mean_weight)
        for weight in weights
    ) / len(weights)

    normalized_deviation = avg_deviation / mean_weight

    return _clamp(1.0 - normalized_deviation)


def _spread_score(features: InvariantFeatures) -> float:
    """Score structural spread across nodes."""
    if not features.node_weights:
        return 0.0

    active_nodes = len(features.node_weights)
    total_weight = sum(features.node_weights.values())

    if total_weight == 0:
        return 0.0

    spread = active_nodes / total_weight

    return _clamp(spread)


def _branching_score(features: InvariantFeatures) -> float:
    """Score outward branching from degree distribution."""
    if not features.degrees:
        return 0.0

    degrees = list(features.degrees.values())
    max_degree = max(degrees)
    mean_degree = sum(degrees) / len(degrees)

    if max_degree == 0:
        return 0.0

    return _clamp((max_degree - mean_degree) / max_degree)


def _clamp(value: float) -> float:
    """Clamp value to [0, 1]."""
    return max(0.0, min(1.0, value))