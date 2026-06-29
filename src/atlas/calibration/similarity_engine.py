"""Atlas Similarity Engine.

Compute structural similarity between calibrated Atlas profiles.

This first version compares ProfileMetrics directly. Later versions can add
graph-native similarity, morphology similarity, and Vedic overlay similarity.
"""

from __future__ import annotations

import math
from dataclasses import asdict
from dataclasses import dataclass
from typing import Any

from atlas.calibration.models import ProfileMetrics
from atlas.calibration.population_statistics import profile_metrics_to_numeric_dict


SIMILARITY_ENGINE_VERSION = "1.0"


@dataclass(frozen=True)
class SimilarityResult:
    """Similarity result between two profiles."""

    version: str
    identity_a: str
    identity_b: str
    similarity: float
    distance: float
    metric_count: int
    component_scores: dict[str, float]
    summary: dict[str, Any]


def compare_profile_metrics(
    profile_a: ProfileMetrics,
    profile_b: ProfileMetrics,
) -> SimilarityResult:
    """Compare two profile metric objects."""
    values_a = profile_metrics_to_numeric_dict(profile_a)
    values_b = profile_metrics_to_numeric_dict(profile_b)

    shared_metrics = sorted(
        set(values_a.keys()) & set(values_b.keys())
    )

    component_scores: dict[str, float] = {}

    for metric in shared_metrics:
        component_scores[metric] = metric_similarity(
            float(values_a[metric]),
            float(values_b[metric]),
        )

    similarity = mean_score(component_scores.values())
    distance = 1.0 - similarity

    return SimilarityResult(
        version=SIMILARITY_ENGINE_VERSION,
        identity_a=profile_a.identity,
        identity_b=profile_b.identity,
        similarity=similarity,
        distance=distance,
        metric_count=len(component_scores),
        component_scores=component_scores,
        summary={
            "definition": "Mean normalized similarity across shared numeric profile metrics.",
            "identity_a": profile_a.identity,
            "identity_b": profile_b.identity,
            "similarity": similarity,
            "distance": distance,
            "metric_count": len(component_scores),
        },
    )


def metric_similarity(
    value_a: float,
    value_b: float,
) -> float:
    """Compute bounded similarity for one numeric metric."""
    if math.isnan(value_a) or math.isnan(value_b):
        return 0.0

    denominator = max(
        abs(value_a),
        abs(value_b),
        1.0,
    )

    difference = abs(value_a - value_b)

    return clamp01(
        1.0 - (difference / denominator)
    )


def mean_score(
    values,
) -> float:
    """Return mean score for iterable values."""
    values = list(values)

    if not values:
        return 0.0

    return sum(values) / len(values)


def clamp01(
    value: float,
) -> float:
    """Clamp value to 0-1."""
    return max(
        0.0,
        min(
            1.0,
            float(value),
        ),
    )


def similarity_result_to_dict(
    result: SimilarityResult,
) -> dict[str, Any]:
    """Convert similarity result to dictionary."""
    return asdict(result)