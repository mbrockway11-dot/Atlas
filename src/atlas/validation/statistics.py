"""Distribution statistics for validation results.

Deliberately dependency-light: scipy is not installed, and the moments used
here are short enough to implement directly, which also keeps them auditable.

Everything is computed from a full score array rather than sampled, because
at corpus scale the exact distribution is affordable and an exact answer
removes a class of doubt from every result built on top of it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np


# Percentiles carried by every distribution. The tails are dense because
# "how unusual is this pair" is a tail question.
DEFAULT_PERCENTILES: tuple[float, ...] = (
    0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0,
    75.0, 90.0, 95.0, 97.5, 99.0, 99.5, 99.9,
)

DEFAULT_HISTOGRAM_BINS = 100


@dataclass(frozen=True, slots=True)
class DistributionSummary:
    """Summary of one score distribution."""

    count: int
    mean: float
    median: float
    stddev: float
    variance: float
    minimum: float
    maximum: float
    skewness: float
    kurtosis: float
    percentiles: dict[str, float]
    histogram_counts: tuple[int, ...]
    histogram_edges: tuple[float, ...]
    distinct_scores: int
    duplicate_score_fraction: float

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "count": self.count,
            "mean": self.mean,
            "median": self.median,
            "stddev": self.stddev,
            "variance": self.variance,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "skewness": self.skewness,
            "kurtosis": self.kurtosis,
            "percentiles": dict(self.percentiles),
            "histogram": {
                "counts": list(self.histogram_counts),
                "edges": list(self.histogram_edges),
            },
            "distinct_scores": self.distinct_scores,
            "duplicate_score_fraction": self.duplicate_score_fraction,
        }


def summarize(
    scores: np.ndarray,
    *,
    percentiles: Sequence[float] = DEFAULT_PERCENTILES,
    bins: int = DEFAULT_HISTOGRAM_BINS,
) -> DistributionSummary:
    """Summarize a score array exactly."""
    values = np.asarray(scores, dtype=np.float64).ravel()

    if values.size == 0:
        raise ValueError("Cannot summarize an empty distribution.")

    mean = float(values.mean())
    variance = float(values.var())
    stddev = float(np.sqrt(variance))

    # Fisher definitions; excess kurtosis, so a normal distribution is 0.
    if stddev > 0:
        centered = (values - mean) / stddev
        skewness = float((centered**3).mean())
        kurtosis = float((centered**4).mean() - 3.0)
    else:
        skewness = 0.0
        kurtosis = 0.0

    quantiles = np.percentile(values, list(percentiles))
    counts, edges = np.histogram(values, bins=bins)

    distinct = int(np.unique(values).size)

    return DistributionSummary(
        count=int(values.size),
        mean=mean,
        median=float(np.median(values)),
        stddev=stddev,
        variance=variance,
        minimum=float(values.min()),
        maximum=float(values.max()),
        skewness=skewness,
        kurtosis=kurtosis,
        percentiles={
            f"p{percentile:g}": float(value)
            for percentile, value in zip(percentiles, quantiles)
        },
        histogram_counts=tuple(int(c) for c in counts),
        histogram_edges=tuple(float(e) for e in edges),
        distinct_scores=distinct,
        duplicate_score_fraction=(
            float(1.0 - distinct / values.size) if values.size else 0.0
        ),
    )


def percentile_of(summary: DistributionSummary, score: float) -> float:
    """Return the population percentile of a score, via the histogram.

    Interpolates within the containing bin. This is what turns a raw
    similarity into a statement about the population -- the deterministic
    score and its percentile are reported separately and never conflated.
    """
    edges = np.asarray(summary.histogram_edges, dtype=np.float64)
    counts = np.asarray(summary.histogram_counts, dtype=np.float64)

    if score <= edges[0]:
        return 0.0

    if score >= edges[-1]:
        return 100.0

    index = int(np.searchsorted(edges, score, side="right") - 1)
    index = max(0, min(index, counts.size - 1))

    below = counts[:index].sum()
    width = edges[index + 1] - edges[index]
    within = (
        counts[index] * ((score - edges[index]) / width) if width > 0 else 0.0
    )

    return float(100.0 * (below + within) / counts.sum())


def top_and_bottom(
    scores: np.ndarray,
    pair_indices: np.ndarray,
    *,
    limit: int = 25,
) -> dict[str, list[tuple[int, int, float]]]:
    """Return the highest- and lowest-scoring pairs.

    ``pair_indices`` is an (n, 2) array of row indices aligned with
    ``scores``.
    """
    values = np.asarray(scores, dtype=np.float64).ravel()
    limit = min(limit, values.size)

    if limit == 0:
        return {"top": [], "bottom": []}

    top_order = np.argpartition(values, -limit)[-limit:]
    top_order = top_order[np.argsort(values[top_order])[::-1]]

    bottom_order = np.argpartition(values, limit - 1)[:limit]
    bottom_order = bottom_order[np.argsort(values[bottom_order])]

    def rows(order: np.ndarray) -> list[tuple[int, int, float]]:
        return [
            (
                int(pair_indices[index, 0]),
                int(pair_indices[index, 1]),
                float(values[index]),
            )
            for index in order
        ]

    return {"top": rows(top_order), "bottom": rows(bottom_order)}


def bootstrap_mean_interval(
    values: np.ndarray,
    *,
    iterations: int = 10_000,
    confidence: float = 0.95,
    seed: int = 0,
) -> dict[str, float]:
    """Return a bootstrap confidence interval for the mean."""
    data = np.asarray(values, dtype=np.float64).ravel()

    if data.size == 0:
        raise ValueError("Cannot bootstrap an empty sample.")

    rng = np.random.default_rng(seed)
    means = np.empty(iterations, dtype=np.float64)

    for index in range(iterations):
        means[index] = data[
            rng.integers(0, data.size, data.size)
        ].mean()

    alpha = (1.0 - confidence) / 2.0

    return {
        "mean": float(data.mean()),
        "lower": float(np.percentile(means, 100 * alpha)),
        "upper": float(np.percentile(means, 100 * (1 - alpha))),
        "confidence": confidence,
        "iterations": iterations,
    }
