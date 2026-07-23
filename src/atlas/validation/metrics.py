"""Alternative similarity geometries for ablation.

Raw cosine over all-positive bounded features compresses hard: the corpus
baseline sits at mean 0.959 with a standard deviation of 0.014, and even a
wholly random name of matched length scores 0.967. Most of that is a shared
positive offset rather than shared structure -- every profile points into the
same corner of the space, so every angle between them is small.

These metrics remove that offset in different ways. Each is a candidate
research lens, not a replacement for the canonical score: the point of the
ablation is to find a geometry that discriminates without destroying the
invariances the encoding is supposed to have.

Every metric here returns a full pairwise matrix from a corpus matrix, and
each is defined so that higher means more similar, so the comparison across
metrics is like for like.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass(frozen=True, slots=True)
class Metric:
    """One named similarity geometry."""

    name: str
    description: str
    higher_is_more_similar: bool
    pairwise: Callable[[np.ndarray], np.ndarray]
    bounded_unit_interval: bool = False


def _unit_rows(matrix: np.ndarray) -> np.ndarray:
    """Return rows scaled to unit length, leaving zero rows alone."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)

    return matrix / np.where(norms == 0.0, 1.0, norms)


def cosine_matrix(matrix: np.ndarray) -> np.ndarray:
    """Plain cosine similarity -- the canonical Atlas geometry."""
    normalized = _unit_rows(matrix)

    return normalized @ normalized.T


def centered_cosine_matrix(matrix: np.ndarray) -> np.ndarray:
    """Cosine after removing the per-feature corpus mean.

    Subtracting the column means removes the shared positive offset that
    every profile carries. What remains is how each profile deviates from
    the typical profile, which is the part that could carry identity.
    """
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    normalized = _unit_rows(centered)

    return normalized @ normalized.T


def standardized_cosine_matrix(matrix: np.ndarray) -> np.ndarray:
    """Cosine after per-feature centering and scaling.

    Also equalizes feature variances, so a high-variance feature cannot
    dominate simply by having a wider range.
    """
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    deviations = centered.std(axis=0, keepdims=True)
    scaled = centered / np.where(deviations == 0.0, 1.0, deviations)
    normalized = _unit_rows(scaled)

    return normalized @ normalized.T


def correlation_matrix(matrix: np.ndarray) -> np.ndarray:
    """Pearson correlation between profiles across features.

    Centering happens per *profile* rather than per feature: it asks whether
    two profiles have the same shape across features, ignoring their overall
    level.
    """
    centered = matrix - matrix.mean(axis=1, keepdims=True)
    normalized = _unit_rows(centered)

    return normalized @ normalized.T


def negative_euclidean_matrix(matrix: np.ndarray) -> np.ndarray:
    """Negated Euclidean distance on standardized features.

    Returned negated so that, like the others, higher means more similar.
    Unbounded below, which is the point: distance does not saturate.
    """
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    deviations = centered.std(axis=0, keepdims=True)
    scaled = centered / np.where(deviations == 0.0, 1.0, deviations)

    squared = (scaled**2).sum(axis=1)
    cross = scaled @ scaled.T
    distances = np.sqrt(
        np.maximum(squared[:, None] + squared[None, :] - 2.0 * cross, 0.0)
    )

    # The diagonal is zero in exact arithmetic but accumulates error through
    # the expansion; set it explicitly so "distance to self" is exactly zero.
    np.fill_diagonal(distances, 0.0)

    return -distances


METRICS: tuple[Metric, ...] = (
    Metric(
        "cosine",
        "Canonical Atlas geometry: cosine over raw bounded features.",
        True,
        cosine_matrix,
        bounded_unit_interval=True,
    ),
    Metric(
        "centered_cosine",
        "Cosine after removing the per-feature corpus mean, which strips "
        "the shared positive offset all profiles carry.",
        True,
        centered_cosine_matrix,
    ),
    Metric(
        "standardized_cosine",
        "Cosine after per-feature centering and scaling to unit variance.",
        True,
        standardized_cosine_matrix,
    ),
    Metric(
        "correlation",
        "Correlation across features within each profile -- shape "
        "agreement, ignoring overall level.",
        True,
        correlation_matrix,
    ),
    Metric(
        "negative_standardized_euclidean",
        "Negated Euclidean distance on standardized features; unbounded, "
        "so it cannot saturate near a ceiling.",
        True,
        negative_euclidean_matrix,
    ),
)


METRICS_BY_NAME = {metric.name: metric for metric in METRICS}


def upper_triangle(matrix: np.ndarray) -> np.ndarray:
    """Return the strict upper triangle of a square matrix, flattened."""
    rows, columns = np.triu_indices(matrix.shape[0], k=1)

    return matrix[rows, columns]


def pair_scores(
    matrix: np.ndarray,
    metric: Metric,
) -> np.ndarray:
    """Return all unordered pair scores under one metric."""
    return upper_triangle(metric.pairwise(matrix))


def spread_ratio(scores: np.ndarray) -> float:
    """Return standard deviation divided by observed range.

    A distribution *shape* statistic, not a compression statistic. It is
    deliberately scale-free -- multiplying every score by a constant leaves
    it unchanged -- so it says nothing about whether scores cluster near a
    ceiling. What it does capture is tail behaviour: a long one-sided tail
    inflates the range relative to the standard deviation and drives the
    ratio down.

    For "does this geometry actually separate things", use
    :func:`separation` against known-positive and known-negative samples.
    """
    values = np.asarray(scores, dtype=np.float64)
    span = float(values.max() - values.min())

    if span <= 0:
        return 0.0

    return float(values.std() / span)


def resolution(
    *,
    invariant_score: float,
    control_score: float,
    population_stddev: float,
) -> float:
    """Return the gap between a known match and a known non-match, in SDs.

    This is the discrimination measure that matters: how far a
    transformation the encoding *should* treat as identical sits above one
    it should treat as unrelated, expressed in population standard
    deviations so geometries on different scales compare directly.
    """
    if population_stddev <= 0:
        return 0.0

    return float((invariant_score - control_score) / population_stddev)


def separation(
    positive: np.ndarray,
    control: np.ndarray,
) -> dict[str, float]:
    """Return standardized separation between two score samples.

    Cohen's d with a pooled standard deviation, plus the probability that a
    randomly drawn positive exceeds a randomly drawn control (the common
    language effect size), which needs no distributional assumption.
    """
    a = np.asarray(positive, dtype=np.float64).ravel()
    b = np.asarray(control, dtype=np.float64).ravel()

    if a.size == 0 or b.size == 0:
        return {"cohens_d": 0.0, "probability_superior": 0.5}

    pooled_variance = (
        (a.size - 1) * a.var(ddof=1) + (b.size - 1) * b.var(ddof=1)
    ) / max(a.size + b.size - 2, 1)
    pooled = float(np.sqrt(pooled_variance)) if pooled_variance > 0 else 0.0

    cohens_d = float((a.mean() - b.mean()) / pooled) if pooled > 0 else 0.0

    # Exact for modest samples; sampled beyond that to bound the cost.
    if a.size * b.size <= 4_000_000:
        superior = float((a[:, None] > b[None, :]).mean())
    else:
        rng = np.random.default_rng(0)
        draws = 1_000_000
        superior = float(
            (
                a[rng.integers(0, a.size, draws)]
                > b[rng.integers(0, b.size, draws)]
            ).mean()
        )

    return {"cohens_d": cohens_d, "probability_superior": superior}
