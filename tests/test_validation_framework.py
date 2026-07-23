"""Tests for the Atlas validation framework.

Two things matter most here. Domain typing must reject the configurations
that cannot answer their own question -- specifically, birth permutation
against identity vectors, which would measure exactly zero by construction.
And the all-pairs run must be deterministic and resumable, because a
baseline that shifts between runs is not a baseline.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from atlas.validation.datasets import (
    ORDERED_CIPHERS,
    ORDERED_FEATURES,
    ORDERED_PLANETS,
    CorpusMatrix,
    build_feature_layout,
    name_strata,
)
from atlas.validation.models import (
    ExperimentConfig,
    ExperimentConfigError,
    ExperimentDomain,
    ExperimentKind,
    config_from_dict,
    load_config,
    validate_config,
)
from atlas.validation.runner import (
    Checkpoint,
    compute_group_scores,
    expected_block_count,
    iter_pair_blocks,
    load_checkpoint,
    run_all_pairs,
    save_checkpoint,
    unit_normalize,
)
from atlas.validation.statistics import (
    percentile_of,
    summarize,
    top_and_bottom,
)


def _base_config(**overrides) -> dict:
    """Return a minimal valid config mapping."""
    payload = {
        "experiment_id": "test_experiment",
        "domain": "identity_vector",
        "kind": "all_pairs_baseline",
        "hypothesis": "A stated hypothesis.",
        "normalization_mode": "raw",
        "metric": "cosine_similarity",
    }
    payload.update(overrides)
    return payload


def _corpus(rows: int = 12, seed: int = 7) -> CorpusMatrix:
    """Build a synthetic corpus matrix with the real feature layout."""
    layout = build_feature_layout()
    rng = np.random.default_rng(seed)

    return CorpusMatrix(
        profile_keys=tuple(f"p{index:03d}" for index in range(rows)),
        profile_names=tuple(f"Person {index}" for index in range(rows)),
        entity_types=("person",) * rows,
        matrix=rng.random((rows, len(layout))),
        feature_layout=layout,
        normalization_mode="raw",
        skipped=(),
    )


# ---------------------------------------------------------------------------
# Domain typing
# ---------------------------------------------------------------------------


def test_identity_vector_rejects_birth_permutation() -> None:
    """The mistake this framework exists to prevent is refused up front.

    Birth data provably does not enter identity vectors, so permuting it
    would measure zero by construction -- not a null result.
    """
    with pytest.raises(ExperimentConfigError, match="name alone"):
        config_from_dict(
            _base_config(options={"birth_permutation": {"shuffle": "date"}})
        )


def test_temporal_experiment_rejects_name_perturbation() -> None:
    """The symmetric error is refused too."""
    with pytest.raises(ExperimentConfigError, match="not from name structure"):
        config_from_dict(
            _base_config(
                domain="temporal_css",
                kind="perturbation",
                options={
                    "name_perturbation": {"kind": "substitution"},
                    "evaluation_date": "2026-01-01",
                },
            )
        )


def test_temporal_experiment_requires_an_evaluation_date() -> None:
    """Without one the result would depend on when it was run."""
    with pytest.raises(ExperimentConfigError, match="evaluation_date"):
        config_from_dict(
            _base_config(domain="temporal_css", kind="cohort_comparison")
        )


def test_temporal_experiment_accepts_birth_permutation() -> None:
    """Birth permutation is valid where birth data actually matters."""
    config = config_from_dict(
        _base_config(
            domain="temporal_css",
            kind="perturbation",
            options={
                "birth_permutation": {"shuffle": "date"},
                "evaluation_date": "2026-01-01",
            },
        )
    )

    assert config.domain is ExperimentDomain.TEMPORAL_CSS


def test_identity_experiment_accepts_name_perturbation() -> None:
    """Name perturbation is the identity-vector analogue."""
    config = config_from_dict(
        _base_config(
            kind="perturbation",
            options={"name_perturbation": {"kind": "substitution"}},
        )
    )

    assert config.domain is ExperimentDomain.IDENTITY_VECTOR


def test_unknown_domain_is_rejected() -> None:
    """A typo in the domain must not silently become a default."""
    with pytest.raises(ExperimentConfigError, match="Unknown domain"):
        config_from_dict(_base_config(domain="identity_vectors"))


def test_missing_domain_is_rejected() -> None:
    """Domain is mandatory from day one."""
    payload = _base_config()
    del payload["domain"]

    with pytest.raises(ExperimentConfigError, match="must declare a domain"):
        config_from_dict(payload)


def test_hypothesis_is_required() -> None:
    """A hypothesis stated after the fact is not a hypothesis."""
    with pytest.raises(ExperimentConfigError, match="hypothesis"):
        config_from_dict(_base_config(hypothesis="   "))


def test_unknown_mode_and_metric_are_rejected() -> None:
    """Silent fallbacks would make results incomparable."""
    with pytest.raises(ExperimentConfigError, match="normalization_mode"):
        config_from_dict(_base_config(normalization_mode="bogus"))

    with pytest.raises(ExperimentConfigError, match="metric"):
        config_from_dict(_base_config(metric="euclidean"))


def test_cohort_comparison_requires_a_cohort() -> None:
    """Comparing cohorts requires cohorts."""
    with pytest.raises(ExperimentConfigError, match="dataset_path"):
        config_from_dict(_base_config(kind="cohort_comparison"))


def test_shipped_baseline_config_is_valid() -> None:
    """The config committed with the framework loads and validates."""
    config = load_config(
        Path("configs/validation/identity_random_pair_baseline_v1.yaml")
    )

    assert config.domain is ExperimentDomain.IDENTITY_VECTOR
    assert config.kind is ExperimentKind.ALL_PAIRS_BASELINE
    assert config.metric == "cosine_similarity"
    assert config.hypothesis.strip()


def test_config_round_trips_through_dict() -> None:
    """A config survives serialization for the experiment artifact."""
    config = config_from_dict(_base_config())
    payload = config.to_dict()

    assert payload["domain"] == "identity_vector"
    assert payload["kind"] == "all_pairs_baseline"
    assert payload["schema_version"].startswith("atlas.validation")


# ---------------------------------------------------------------------------
# Pair enumeration
# ---------------------------------------------------------------------------


def test_pair_count_matches_the_formula() -> None:
    """Every unordered pair appears exactly once."""
    corpus = _corpus(rows=25)
    pairs, scores, _ = run_all_pairs(corpus, block_size=7)

    assert pairs.shape[0] == 25 * 24 // 2 == corpus.pair_count
    assert scores.size == pairs.shape[0]


def test_pairs_are_unique_and_upper_triangular() -> None:
    """No pair is duplicated and none is self-paired."""
    corpus = _corpus(rows=20)
    pairs, _, _ = run_all_pairs(corpus, block_size=6)

    assert np.all(pairs[:, 0] < pairs[:, 1])
    assert len({tuple(row) for row in pairs}) == pairs.shape[0]


@pytest.mark.parametrize("block_size", [1, 3, 8, 64])
def test_pair_enumeration_is_independent_of_block_size(
    block_size: int,
) -> None:
    """Which pairs exist, and in what order, never depends on block size."""
    corpus = _corpus(rows=17)

    reference_pairs, _, _ = run_all_pairs(corpus, block_size=17)
    pairs, _, _ = run_all_pairs(corpus, block_size=block_size)

    assert np.array_equal(pairs, reference_pairs)


@pytest.mark.parametrize("block_size", [1, 3, 8, 64])
def test_scores_are_numerically_equivalent_across_block_sizes(
    block_size: int,
) -> None:
    """Scores agree to within a few ULPs across block sizes.

    Not bit-exact, and deliberately not asserted as such: BLAS chooses
    different summation orders for different matrix shapes, so the last bits
    of a dot product depend on how the work was blocked. The observed spread
    is ~4e-16, about two ULPs.

    The reproduction contract is therefore stated in terms of the config:
    ``block_size`` is recorded in provenance, and a re-run with the same
    config is bit-exact (see the test below). Anyone comparing runs across
    different block sizes should compare to tolerance, not equality.
    """
    corpus = _corpus(rows=17)

    _, reference_scores, _ = run_all_pairs(corpus, block_size=17)
    _, scores, _ = run_all_pairs(corpus, block_size=block_size)

    assert np.allclose(scores, reference_scores, rtol=0, atol=5e-15)


def test_repeated_runs_are_identical() -> None:
    """A baseline that moves between runs is not a baseline."""
    corpus = _corpus(rows=30)

    first_pairs, first_scores, _ = run_all_pairs(corpus, block_size=8)
    second_pairs, second_scores, _ = run_all_pairs(corpus, block_size=8)

    assert np.array_equal(first_pairs, second_pairs)
    assert np.array_equal(first_scores, second_scores)


def test_resumed_run_matches_the_tail_of_a_full_run() -> None:
    """Resuming from a block boundary reproduces the remaining pairs."""
    corpus = _corpus(rows=24)
    block_size = 6

    full_pairs, full_scores, _ = run_all_pairs(corpus, block_size=block_size)

    prefix_pairs = np.vstack(
        [
            block.pair_indices
            for _, block in iter_pair_blocks(
                corpus.matrix, block_size=block_size
            )
        ][:2]
    )

    resumed_pairs, resumed_scores, _ = run_all_pairs(
        corpus, block_size=block_size, start_block=2
    )

    assert np.array_equal(
        np.vstack((prefix_pairs, resumed_pairs)), full_pairs
    )
    assert resumed_scores.size == full_scores.size - prefix_pairs.shape[0]


def test_expected_block_count() -> None:
    """Block accounting matches the enumeration."""
    assert expected_block_count(0, 10) == 0
    assert expected_block_count(10, 10) == 1
    assert expected_block_count(11, 10) == 2
    assert expected_block_count(2122, 256) == 9


# ---------------------------------------------------------------------------
# Metric behaviour
# ---------------------------------------------------------------------------


def test_identical_rows_score_one() -> None:
    """A profile compared with a copy of itself is a perfect match."""
    layout = build_feature_layout()
    row = np.random.default_rng(1).random(len(layout))

    corpus = CorpusMatrix(
        profile_keys=("a", "b"),
        profile_names=("A", "B"),
        entity_types=("person", "person"),
        matrix=np.vstack((row, row)),
        feature_layout=layout,
        normalization_mode="raw",
        skipped=(),
    )

    _, scores, _ = run_all_pairs(corpus, block_size=2)

    assert scores[0] == pytest.approx(1.0)


def test_unit_normalize_leaves_zero_rows_finite() -> None:
    """A zero row must not produce NaN and poison the whole matrix."""
    matrix = np.array([[0.0, 0.0], [3.0, 4.0]])
    normalized = unit_normalize(matrix)

    assert np.isfinite(normalized).all()
    assert normalized[1] == pytest.approx([0.6, 0.8])


def test_group_decomposition_covers_ciphers_and_planets() -> None:
    """Per-cipher and per-planet scores are produced for each group."""
    corpus = _corpus(rows=10)
    pairs, _, _ = run_all_pairs(corpus, block_size=5)

    groups = compute_group_scores(corpus, sample_pairs=pairs[:20])

    for cipher in ORDERED_CIPHERS:
        assert groups[f"cipher:{cipher}"].size == 20

    for planet in ORDERED_PLANETS:
        assert groups[f"planet:{planet}"].size == 20


def test_feature_layout_is_complete_and_ordered() -> None:
    """The column layout is fixed, and its size is the product of parts."""
    layout = build_feature_layout()

    assert len(layout) == (
        len(ORDERED_CIPHERS) * len(ORDERED_PLANETS) * len(ORDERED_FEATURES)
    )
    assert layout == tuple(sorted(layout, key=layout.index))
    assert len(set(layout)) == len(layout)


def test_block_selects_the_right_columns() -> None:
    """Cipher and planet slices select disjoint, correctly sized blocks."""
    corpus = _corpus(rows=4)

    cipher_block = corpus.block(ORDERED_CIPHERS[0], None)
    planet_block = corpus.block(None, ORDERED_PLANETS[0])

    assert cipher_block.shape[1] == (
        len(ORDERED_PLANETS) * len(ORDERED_FEATURES)
    )
    assert planet_block.shape[1] == (
        len(ORDERED_CIPHERS) * len(ORDERED_FEATURES)
    )


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def test_summary_reports_exact_moments() -> None:
    """Summary statistics are computed, not estimated."""
    values = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    summary = summarize(values, bins=5)

    assert summary.count == 5
    assert summary.mean == pytest.approx(2.0)
    assert summary.median == pytest.approx(2.0)
    assert summary.minimum == 0.0
    assert summary.maximum == 4.0
    assert summary.distinct_scores == 5
    assert summary.duplicate_score_fraction == pytest.approx(0.0)


def test_summary_detects_duplicate_scores() -> None:
    """Duplicate-score frequency is part of the collision picture."""
    summary = summarize(np.array([1.0, 1.0, 1.0, 2.0]), bins=4)

    assert summary.distinct_scores == 2
    assert summary.duplicate_score_fraction == pytest.approx(0.5)


def test_summary_rejects_empty_input() -> None:
    """An empty distribution has no summary."""
    with pytest.raises(ValueError):
        summarize(np.array([]))


def test_percentile_of_is_monotonic() -> None:
    """Population percentile increases with score."""
    rng = np.random.default_rng(3)
    summary = summarize(rng.normal(size=10_000), bins=100)

    low = percentile_of(summary, summary.percentiles["p10"])
    mid = percentile_of(summary, summary.percentiles["p50"])
    high = percentile_of(summary, summary.percentiles["p90"])

    assert 0.0 <= low < mid < high <= 100.0


def test_top_and_bottom_are_ordered() -> None:
    """Extremes come back sorted, highest and lowest first."""
    scores = np.array([0.1, 0.9, 0.5, 0.3])
    pairs = np.array([[0, 1], [0, 2], [1, 2], [1, 3]])

    extremes = top_and_bottom(scores, pairs, limit=2)

    assert [row[2] for row in extremes["top"]] == [0.9, 0.5]
    assert [row[2] for row in extremes["bottom"]] == [0.1, 0.3]


def test_name_strata_describe_shape() -> None:
    """Name descriptors used for confounder checks are computed correctly."""
    strata = name_strata(["Ada Lovelace", "Plato", "Jose Ramon de la Cruz"])

    assert list(strata["token_count"]) == [2, 1, 5]
    assert strata["character_length"][1] == len("Plato")
    assert strata["is_ascii"].all()


# ---------------------------------------------------------------------------
# Checkpoints
# ---------------------------------------------------------------------------


def test_checkpoint_round_trip(tmp_path: Path) -> None:
    """Resume state survives a save/load cycle."""
    checkpoint = Checkpoint(
        experiment_id="x",
        corpus_fingerprint="10:raw",
        block_size=4,
        completed_blocks=2,
        total_blocks=3,
        pairs_written=17,
    )

    path = save_checkpoint(checkpoint, tmp_path / "checkpoint.json")
    restored = load_checkpoint(path)

    assert restored == checkpoint


def test_damaged_checkpoint_is_ignored(tmp_path: Path) -> None:
    """A corrupt checkpoint restarts the run rather than crashing it."""
    path = tmp_path / "checkpoint.json"
    path.write_text("{not json", encoding="utf-8")

    assert load_checkpoint(path) is None


def test_absent_checkpoint_is_none(tmp_path: Path) -> None:
    """No checkpoint simply means no resume."""
    assert load_checkpoint(tmp_path / "absent.json") is None
