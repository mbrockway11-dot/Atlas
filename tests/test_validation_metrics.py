"""Tests for alternative similarity geometries.

The ablation only means something if each metric is what it claims to be, and
if the invariance check is capable of failing. These pin both.
"""

from __future__ import annotations

import numpy as np
import pytest

from atlas.validation.metrics import (
    METRICS,
    METRICS_BY_NAME,
    centered_cosine_matrix,
    correlation_matrix,
    cosine_matrix,
    resolution,
    spread_ratio,
    negative_euclidean_matrix,
    pair_scores,
    separation,
    standardized_cosine_matrix,
    upper_triangle,
)


def _matrix(rows: int = 40, columns: int = 20, seed: int = 3) -> np.ndarray:
    """Return an all-positive matrix resembling Atlas features."""
    return np.random.default_rng(seed).random((rows, columns))


# ---------------------------------------------------------------------------
# Metric identities
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("metric", METRICS, ids=lambda m: m.name)
def test_self_similarity_is_maximal(metric) -> None:
    """A profile is at least as similar to itself as to anything else."""
    matrix = _matrix()
    scores = metric.pairwise(matrix)

    diagonal = np.diag(scores)

    for row in range(matrix.shape[0]):
        others = np.delete(scores[row], row)
        assert diagonal[row] >= others.max() - 1e-9


@pytest.mark.parametrize("metric", METRICS, ids=lambda m: m.name)
def test_metrics_are_symmetric(metric) -> None:
    """Similarity does not depend on argument order."""
    scores = metric.pairwise(_matrix())

    assert np.allclose(scores, scores.T, atol=1e-12)


def test_cosine_matches_manual_computation() -> None:
    """The canonical metric is plain cosine, verifiably."""
    matrix = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    scores = cosine_matrix(matrix)

    assert scores[0, 1] == pytest.approx(0.0)
    assert scores[0, 2] == pytest.approx(1.0 / np.sqrt(2))


def test_centering_removes_the_shared_offset() -> None:
    """Centered cosine spreads scores that plain cosine compresses.

    Reproduces the corpus situation: all-positive features with a large
    common component and small differences.
    """
    rng = np.random.default_rng(1)
    offset = np.full((60, 25), 0.9)
    matrix = offset + rng.normal(0.0, 0.01, size=(60, 25))

    plain = upper_triangle(cosine_matrix(matrix))
    centered = upper_triangle(centered_cosine_matrix(matrix))

    assert plain.mean() > 0.99
    assert centered.std() > plain.std() * 10


def test_correlation_ignores_profile_level() -> None:
    """Adding a constant to a profile does not change correlation."""
    matrix = _matrix(rows=10, columns=15)
    shifted = matrix.copy()
    shifted[0] = shifted[0] + 5.0

    original = correlation_matrix(matrix)[0, 1]
    lifted = correlation_matrix(shifted)[0, 1]

    assert lifted == pytest.approx(original, abs=1e-9)


def test_standardized_cosine_equalizes_feature_scale() -> None:
    """Rescaling one feature must not change standardized similarity."""
    matrix = _matrix(rows=30, columns=10)
    rescaled = matrix.copy()
    rescaled[:, 0] *= 1000.0

    original = upper_triangle(standardized_cosine_matrix(matrix))
    scaled = upper_triangle(standardized_cosine_matrix(rescaled))

    assert np.allclose(original, scaled, atol=1e-9)


def test_negative_euclidean_is_zero_on_the_diagonal() -> None:
    """Distance from a profile to itself is zero, negated."""
    scores = negative_euclidean_matrix(_matrix())

    assert np.allclose(np.diag(scores), 0.0, atol=1e-9)


def test_negative_euclidean_orders_like_distance() -> None:
    """A nearer profile scores higher once negated."""
    matrix = np.array([[0.0, 0.0], [1.0, 0.0], [10.0, 0.0], [0.1, 0.0]])
    scores = negative_euclidean_matrix(matrix)

    assert scores[0, 3] > scores[0, 1] > scores[0, 2]


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------


def test_spread_ratio_is_scale_and_shift_free() -> None:
    """It is a shape statistic: rescaling and shifting leave it unchanged.

    Worth pinning explicitly, because it means spread_ratio says nothing
    about whether scores cluster near a ceiling. Compression is measured by
    resolution against known positives and negatives instead.
    """
    values = np.random.default_rng(2).normal(0.0, 1.0, size=2_000)

    assert spread_ratio(values * 100.0) == pytest.approx(spread_ratio(values))
    assert spread_ratio(values + 50.0) == pytest.approx(spread_ratio(values))


def test_spread_ratio_detects_tail_shape() -> None:
    """A long one-sided tail lowers the ratio relative to a symmetric one."""
    rng = np.random.default_rng(7)
    symmetric = rng.normal(0.0, 1.0, size=20_000)
    tailed = -rng.exponential(1.0, size=20_000)

    assert spread_ratio(tailed) < spread_ratio(symmetric)


def test_spread_ratio_of_constant_scores_is_zero() -> None:
    """No spread, and no division by zero."""
    assert spread_ratio(np.full(100, 0.5)) == 0.0


def test_resolution_measures_the_match_nonmatch_gap() -> None:
    """Resolution is the known-match minus known-non-match gap, in SDs."""
    assert resolution(
        invariant_score=1.0, control_score=0.9, population_stddev=0.05
    ) == pytest.approx(2.0)


def test_resolution_is_zero_without_spread() -> None:
    """A degenerate population cannot resolve anything."""
    assert resolution(
        invariant_score=1.0, control_score=0.0, population_stddev=0.0
    ) == 0.0


def test_separation_detects_a_real_difference() -> None:
    """Two clearly separated samples produce a large effect size."""
    rng = np.random.default_rng(4)
    high = rng.normal(1.0, 0.1, size=500)
    low = rng.normal(0.0, 0.1, size=500)

    result = separation(high, low)

    assert result["cohens_d"] > 5.0
    assert result["probability_superior"] > 0.99


def test_separation_of_identical_distributions_is_neutral() -> None:
    """Indistinguishable samples give d near zero and p near one half."""
    rng = np.random.default_rng(6)
    a = rng.normal(0.0, 1.0, size=2_000)
    b = rng.normal(0.0, 1.0, size=2_000)

    result = separation(a, b)

    assert abs(result["cohens_d"]) < 0.15
    assert result["probability_superior"] == pytest.approx(0.5, abs=0.05)


def test_separation_handles_empty_samples() -> None:
    """An empty arm is reported neutrally rather than crashing."""
    result = separation(np.array([]), np.array([1.0, 2.0]))

    assert result["cohens_d"] == 0.0
    assert result["probability_superior"] == 0.5


def test_pair_scores_returns_every_unordered_pair() -> None:
    """Pair extraction matches the n(n-1)/2 count."""
    matrix = _matrix(rows=12)

    for metric in METRICS:
        assert pair_scores(matrix, metric).size == 12 * 11 // 2


def test_metric_registry_is_consistent() -> None:
    """Every metric is registered under its own name."""
    assert set(METRICS_BY_NAME) == {metric.name for metric in METRICS}

    for name, metric in METRICS_BY_NAME.items():
        assert metric.name == name
        assert metric.description.strip()
        assert metric.higher_is_more_similar
