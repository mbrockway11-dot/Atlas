"""Tests for matched percentiles, perturbations, residuals, and neighbours.

The matched percentile is the load-bearing piece: the baseline showed a
global percentile can be high purely because two names share a shape, so
these tests pin that a matched percentile compares like with like.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from atlas.validation.datasets import build_feature_layout, cosine
from atlas.validation.matching import (
    MATCHED_INDEX_SCHEMA,
    MatchedPercentileIndex,
    build_matched_index,
    length_difference_bucket,
    load_matched_index,
    sample_matched_controls,
    save_matched_index,
    stratum_keys,
)
from atlas.validation.neighbors import summarize_false_neighbors, NeighborRecord
from atlas.validation.perturbations import (
    INVARIANCE_TRANSFORMATIONS,
    Expectation,
    build_perturbations,
    delete_characters,
    insert_characters,
    length_matched_random,
    shuffle_characters,
    substitute,
    transpose_adjacent,
)
from atlas.validation.residuals import (
    RESIDUAL_MODEL_SCHEMA,
    build_design_matrix,
    fit_residual_model,
    load_residual_model,
    partial_correlation,
    save_residual_model,
    spearman_correlation,
)


# ---------------------------------------------------------------------------
# Matched percentiles
# ---------------------------------------------------------------------------


def test_stratum_keys_are_order_independent() -> None:
    """A pair's stratum does not depend on which profile is listed first."""
    tokens = np.array([2, 3], dtype=np.int32)
    lengths = np.array([10, 20], dtype=np.int32)

    forward = stratum_keys(
        token_counts=tokens,
        char_lengths=lengths,
        pair_indices=np.array([[0, 1]]),
    )
    reverse = stratum_keys(
        token_counts=tokens,
        char_lengths=lengths,
        pair_indices=np.array([[1, 0]]),
    )

    assert forward[0] == reverse[0]


def test_length_difference_buckets_are_ordered() -> None:
    """Bucket labels partition the range without gaps."""
    assert str(length_difference_bucket(0)) == "0-2"
    assert str(length_difference_bucket(2)) == "0-2"
    assert str(length_difference_bucket(3)) == "3-5"
    assert str(length_difference_bucket(10)) == "6-10"
    assert str(length_difference_bucket(20)) == "11-20"
    assert str(length_difference_bucket(99)) == "21+"


def test_matched_percentile_differs_from_global() -> None:
    """The whole point: a score can be globally high, locally ordinary.

    Two strata with different score levels. A value that is extreme against
    the pooled population is unremarkable inside the higher stratum.
    """
    rng = np.random.default_rng(5)

    high = rng.normal(0.98, 0.005, size=5_000)
    low = rng.normal(0.90, 0.005, size=5_000)

    scores = np.concatenate((high, low))
    labels = np.array(["high"] * high.size + ["low"] * low.size)

    index = build_matched_index(scores=scores, labels=labels)

    probe = 0.98
    matched = index.matched_percentile(probe, "high")
    pooled = index.pooled.percentile_of(probe)

    assert pooled > 70.0
    assert matched < 60.0
    assert matched < pooled


def test_small_strata_fall_back_to_pooled() -> None:
    """A percentile from a handful of pairs is noise wearing a number."""
    scores = np.concatenate(
        (np.linspace(0.0, 1.0, 1_000), np.array([0.5, 0.51, 0.52]))
    )
    labels = np.array(["big"] * 1_000 + ["tiny"] * 3)

    index = build_matched_index(scores=scores, labels=labels)

    assert "tiny" not in index.strata
    assert index.stratum_for("tiny") is index.pooled


def test_matched_index_round_trip(tmp_path: Path) -> None:
    """The index survives a save/load cycle."""
    rng = np.random.default_rng(11)
    scores = rng.random(3_000)
    labels = np.array(["a", "b", "c"] * 1_000)

    index = build_matched_index(scores=scores, labels=labels)
    path = save_matched_index(index, tmp_path / "index.json")
    restored = load_matched_index(path)

    assert restored.schema_version == MATCHED_INDEX_SCHEMA
    assert restored.strata.keys() == index.strata.keys()
    assert restored.matched_percentile(0.5, "a") == pytest.approx(
        index.matched_percentile(0.5, "a")
    )


def test_matched_index_rejects_foreign_schema() -> None:
    """An unknown index version is refused rather than guessed at."""
    rng = np.random.default_rng(2)
    index = build_matched_index(
        scores=rng.random(1_000), labels=np.array(["x"] * 1_000)
    )
    payload = index.to_dict()
    payload["schema_version"] = "atlas.validation.matched-percentile-index.v99"

    with pytest.raises(ValueError, match="Unsupported"):
        MatchedPercentileIndex.from_dict(payload)


def test_percentile_bounds_are_respected() -> None:
    """Scores outside the observed range clamp to 0 and 100."""
    scores = np.linspace(0.2, 0.8, 2_000)
    index = build_matched_index(
        scores=scores, labels=np.array(["s"] * scores.size)
    )

    assert index.matched_percentile(0.0, "s") == 0.0
    assert index.matched_percentile(1.0, "s") == 100.0


def test_matched_controls_share_the_positive_stratum() -> None:
    """Controls are drawn from the positive pair's own stratum."""
    candidates = np.array([[0, 1], [2, 3], [4, 5], [6, 7]])
    labels = np.array(["A", "A", "B", "A"])

    matched = sample_matched_controls(
        positive_pairs=[(0, 1)],
        labels_by_pair={(0, 1): "A"},
        candidate_pairs=candidates,
        candidate_labels=labels,
        controls_per_positive=2,
        seed=3,
    )

    controls = matched[(0, 1)]

    assert len(controls) == 2
    assert (0, 1) not in controls
    assert all(tuple(c) in {(2, 3), (6, 7)} for c in controls)


# ---------------------------------------------------------------------------
# Perturbations
# ---------------------------------------------------------------------------


def test_length_preserving_edits_preserve_length() -> None:
    """Substitution and transposition must not change character count."""
    rng = np.random.default_rng(1)
    name = "Nikola Tesla"

    assert len(substitute(name, count=2, rng=rng)) == len(name)
    assert len(transpose_adjacent(name, count=2, rng=rng)) == len(name)
    assert len(shuffle_characters(name, rng=rng)) == len(name)
    assert len(length_matched_random(name, rng=rng)) == len(name)


def test_length_changing_edits_change_length() -> None:
    """Deletion and insertion move the length by the requested amount."""
    rng = np.random.default_rng(1)
    name = "Nikola Tesla"

    assert len(delete_characters(name, count=3, rng=rng)) == len(name) - 3
    assert len(insert_characters(name, count=3, rng=rng)) == len(name) + 3


def test_shuffle_preserves_the_letter_multiset() -> None:
    """A shuffle rearranges letters without adding or removing any."""
    rng = np.random.default_rng(4)
    name = "Ada Lovelace"

    shuffled = shuffle_characters(name, rng=rng)

    assert sorted(shuffled.replace(" ", "")) == sorted(name.replace(" ", ""))


def test_perturbations_are_deterministic_given_a_seed() -> None:
    """The whole experiment must reproduce, so edits must be seeded."""
    name = "Grace Hopper"

    first = substitute(name, count=2, rng=np.random.default_rng(9))
    second = substitute(name, count=2, rng=np.random.default_rng(9))

    assert first == second


def test_substitution_actually_substitutes() -> None:
    """A substitution replaces a letter with a different one."""
    name = "aaaa"
    mutated = substitute(name, count=4, rng=np.random.default_rng(0))

    assert len(mutated) == 4
    assert all(ch != "a" for ch in mutated)


def test_every_invariance_transformation_declares_an_expectation() -> None:
    """Predictions are made in advance, never inferred from results."""
    assert INVARIANCE_TRANSFORMATIONS

    for transformation in INVARIANCE_TRANSFORMATIONS:
        assert isinstance(transformation.expectation, Expectation)
        assert transformation.rationale.strip()


def test_perturbation_catalogue_is_graded() -> None:
    """Graded perturbations cover a range of severities."""
    perturbations = build_perturbations(max_severity=3)
    severities = {p.severity for p in perturbations if p.severity < 90}

    assert severities == {1, 2, 3}
    assert any(p.preserves_length for p in perturbations)
    assert any(not p.preserves_length for p in perturbations)


# ---------------------------------------------------------------------------
# Residuals
# ---------------------------------------------------------------------------


def _structural_fixture(size: int = 2_000, seed: int = 6):
    """Return design inputs plus scores driven partly by structure."""
    rng = np.random.default_rng(seed)
    n = 200

    char_lengths = rng.integers(5, 40, size=n).astype(np.int32)
    token_counts = rng.integers(1, 5, size=n).astype(np.int32)
    is_ascii = np.ones(n, dtype=bool)

    pairs = rng.integers(0, n, size=(size, 2))
    pairs = pairs[pairs[:, 0] != pairs[:, 1]]

    design = build_design_matrix(
        char_lengths=char_lengths,
        token_counts=token_counts,
        is_ascii=is_ascii,
        pair_indices=pairs,
    )

    # Score falls with length difference, plus noise.
    scores = (
        0.98
        - 0.002 * design[:, 1]
        + rng.normal(0.0, 0.005, size=design.shape[0])
    )

    return design, scores


def test_residual_model_recovers_structural_dependence() -> None:
    """The model detects a score that really does depend on length."""
    design, scores = _structural_fixture()
    model = fit_residual_model(scores=scores, design=design)

    assert model.r_squared > 0.5

    # Coefficient on absolute length difference is negative, as constructed.
    coefficients = dict(
        zip(model.feature_names, model.coefficients)
    )
    assert coefficients["abs_length_difference"] < 0


def test_residuals_remove_the_structural_component() -> None:
    """Residuals are uncorrelated with the predictor they control for."""
    design, scores = _structural_fixture()
    model = fit_residual_model(scores=scores, design=design)

    residuals = model.residuals(scores=scores, design=design)
    correlation = float(np.corrcoef(design[:, 1], residuals)[0, 1])

    assert abs(correlation) < 1e-6
    assert abs(float(residuals.mean())) < 1e-9


def test_residual_model_round_trip(tmp_path: Path) -> None:
    """A fitted model persists and reloads."""
    design, scores = _structural_fixture()
    model = fit_residual_model(scores=scores, design=design)

    path = save_residual_model(model, tmp_path / "model.json")
    restored = load_residual_model(path)

    assert restored.schema_version == RESIDUAL_MODEL_SCHEMA
    assert restored.coefficients == pytest.approx(model.coefficients)
    assert restored.r_squared == pytest.approx(model.r_squared)


def test_partial_correlation_removes_a_common_cause() -> None:
    """Controlling for the driver collapses a spurious correlation."""
    rng = np.random.default_rng(8)
    driver = rng.normal(size=3_000)

    x = driver + rng.normal(0, 0.01, size=3_000)
    y = driver + rng.normal(0, 0.01, size=3_000)

    raw = float(np.corrcoef(x, y)[0, 1])
    partial = partial_correlation(
        target=y, predictor=x, controls=driver.reshape(-1, 1)
    )

    assert raw > 0.9
    assert abs(partial) < 0.3


def test_spearman_matches_pearson_on_ranks() -> None:
    """A monotone nonlinear relationship reads as near-perfect rank order."""
    x = np.linspace(1, 100, 500)
    y = np.log(x)

    assert spearman_correlation(x, y) == pytest.approx(1.0, abs=1e-9)


def test_spearman_handles_ties() -> None:
    """Tied values must not produce a degenerate result."""
    x = np.array([1.0, 1.0, 2.0, 2.0, 3.0])
    y = np.array([1.0, 1.0, 2.0, 2.0, 3.0])

    assert spearman_correlation(x, y) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Neighbour audit
# ---------------------------------------------------------------------------


def _record(matched: float, length_difference: int = 1) -> NeighborRecord:
    """Build a neighbour record with the given matched percentile."""
    return NeighborRecord(
        profile_a="a",
        profile_b="b",
        name_a="A",
        name_b="B",
        score=0.99,
        global_percentile=99.9,
        matched_percentile=matched,
        stratum="2+2|len:0-2",
        length_difference=length_difference,
        token_difference=0,
        cipher_scores={"ordinal": 0.99, "hebrew_literal": 0.95},
        planet_scores={"Sun": 0.98, "Moon": 0.97},
    )


def test_false_neighbor_summary_separates_explained_from_extreme() -> None:
    """A neighbour ordinary within its stratum is explained by structure."""
    records = [_record(50.0), _record(60.0), _record(99.0), _record(99.5)]

    summary = summarize_false_neighbors(records)

    assert summary["count"] == 4
    assert summary["explained_by_structure"] == 2
    assert summary["still_extreme_when_matched"] == 2
    assert summary["explained_fraction"] == pytest.approx(0.5)


def test_false_neighbor_summary_reports_dominant_contributors() -> None:
    """The audit names which cipher and planet drove the agreement."""
    summary = summarize_false_neighbors([_record(99.0)])

    assert summary["dominant_cipher_counts"] == {"ordinal": 1}
    assert summary["dominant_planet_counts"] == {"Sun": 1}


def test_empty_neighbor_summary_is_safe() -> None:
    """No records is a valid, reportable outcome."""
    assert summarize_false_neighbors([])["count"] == 0


# ---------------------------------------------------------------------------
# Name vectorization
# ---------------------------------------------------------------------------


def test_cosine_handles_zero_vectors() -> None:
    """A zero vector cannot produce NaN."""
    layout = build_feature_layout()
    zero = np.zeros(len(layout))
    other = np.ones(len(layout))

    assert cosine(zero, other) == 0.0


def test_cosine_of_identical_vectors_is_one() -> None:
    """Self-similarity is 1.0 up to floating point."""
    values = np.random.default_rng(0).random(50)

    assert cosine(values, values) == pytest.approx(1.0)
