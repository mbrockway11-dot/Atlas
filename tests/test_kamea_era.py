"""Tests for blocked era predictability of R1 encodings.

Accepting static slow bodies made a static cell an era marker, so this is
Temporal 2 v1's leakage in R1 form. These tests pin the two things that keep
the measurement honest: validation blocked by calendar year, and mutual
information kept separate from finite-sample accuracy.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from atlas.validation.kamea_era import (
    EARLY_ERA,
    LATE_ERA,
    EraError,
    balanced_accuracy,
    binary_era_labels,
    blocked_accuracy,
    decade_labels,
    era_association,
    year_blocked_folds,
)


def _era_cohort(per_era: int = 40) -> tuple[list[datetime], list[str]]:
    """Return a deterministic cohort spanning both eras."""
    instants = [
        EARLY_ERA[0] + timedelta(days=91 * index) for index in range(per_era)
    ] + [LATE_ERA[0] + timedelta(days=91 * index) for index in range(per_era)]

    return binary_era_labels(sorted(instants))


# ---------------------------------------------------------------------------
# Blocking
# ---------------------------------------------------------------------------


def test_no_calendar_year_spans_a_split() -> None:
    """The guarantee that makes the measurement meaningful.

    A random split would put timestamps a day apart -- with effectively
    identical Saturn state -- in both train and test, inflating accuracy for
    exactly the bodies whose leakage is at issue.
    """
    instants, labels = _era_cohort()
    folds = year_blocked_folds(instants, labels, folds=4)

    years_by_fold = [
        {instants[index].year for index in fold} for fold in folds
    ]

    for position, years in enumerate(years_by_fold):
        others = set().union(
            *(
                other
                for index, other in enumerate(years_by_fold)
                if index != position
            )
        )

        assert not (years & others), "a year appeared in two folds"


def test_every_fold_carries_every_label() -> None:
    """Chunking within each label keeps both eras present in each fold."""
    instants, labels = _era_cohort()
    folds = year_blocked_folds(instants, labels, folds=4)

    for fold in folds:
        assert {labels[index] for index in fold} == {"early", "late"}


def test_blocked_validation_needs_at_least_two_folds() -> None:
    """A single fold has no held-out data."""
    instants, labels = _era_cohort()

    with pytest.raises(EraError, match="at least two folds"):
        year_blocked_folds(instants, labels, folds=1)


def test_labels_cover_only_the_two_declared_eras() -> None:
    """Instants between the eras are excluded, not silently relabelled."""
    between = datetime(1995, 6, 1, tzinfo=UTC)
    kept, labels = binary_era_labels([EARLY_ERA[0], between, LATE_ERA[0]])

    assert len(kept) == 2
    assert labels == ["early", "late"]
    assert between not in kept


def test_decade_labels_are_stable() -> None:
    """The multi-era task labels by decade."""
    assert decade_labels([datetime(1974, 3, 1, tzinfo=UTC)]) == ["1970s"]
    assert decade_labels([datetime(2019, 12, 31, tzinfo=UTC)]) == ["2010s"]


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def test_balanced_accuracy_ignores_class_imbalance() -> None:
    """Always guessing the majority scores 0.5, not the majority share."""
    truth = ["a"] * 90 + ["b"] * 10

    assert balanced_accuracy(truth, ["a"] * 100) == pytest.approx(0.5)
    assert balanced_accuracy(truth, truth) == pytest.approx(1.0)


def test_a_perfectly_predictive_signature_is_detected() -> None:
    """A signature that encodes the era is found."""
    instants, labels = _era_cohort()
    signatures = [(label,) for label in labels]

    result = blocked_accuracy(signatures, instants, labels)

    assert result["balanced_accuracy"] == pytest.approx(1.0)
    assert result["unseen_class_rate"] == pytest.approx(0.0)


def test_a_constant_signature_predicts_nothing() -> None:
    """A stationary body cannot separate eras, and scores at chance."""
    instants, labels = _era_cohort()

    result = blocked_accuracy([("x",)] * len(instants), instants, labels)

    assert result["balanced_accuracy"] == pytest.approx(0.5)


def test_unique_signatures_report_their_unseen_rate() -> None:
    """Near-unique classes inflate association but cannot generalize.

    Reported so that a high mutual information from a finely partitioned
    encoding is not mistaken for usable separability.
    """
    instants, labels = _era_cohort()
    signatures = [(index,) for index in range(len(instants))]

    result = blocked_accuracy(signatures, instants, labels)

    assert result["unseen_class_rate"] == pytest.approx(1.0)
    assert result["balanced_accuracy"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Association
# ---------------------------------------------------------------------------


def test_association_reports_information_and_separability_apart() -> None:
    """The two must not be collapsed: they can disagree, informatively."""
    instants, labels = _era_cohort()
    signatures = [(index,) for index in range(len(instants))]

    result = era_association(
        signatures, instants, labels, permutations=50
    )

    # Every signature unique: mutual information is maximal by construction,
    # while nothing generalizes to a held-out year block.
    assert result["mutual_information_nats"] > 0.5
    assert result["balanced_accuracy"] == pytest.approx(0.5)
    # The block-permutation null is what makes the inflated estimate
    # interpretable rather than impressive.
    assert result["mi_p_value"] > 0.05


def test_a_constant_signature_has_no_association() -> None:
    """No information, no separability, no significance."""
    instants, labels = _era_cohort()

    result = era_association(
        [("x",)] * len(instants), instants, labels, permutations=50
    )

    assert result["mutual_information_nats"] == pytest.approx(0.0)
    assert result["mi_p_value"] > 0.05
