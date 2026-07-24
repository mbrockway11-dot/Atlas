"""Tests for the preregistered R1-Q decision rule.

The rule exists to stop the large cohort from being read as whatever it
happens to show, so these tests pin the rule's shape rather than any
particular measurement: what counts as evidence against quantization
dominance, and which outcomes must stay separate.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from atlas.validation.kamea_baselines import encode_cohort, irregular_cohort
from atlas.validation.kamea_era import decade_labels
from atlas.validation.r1q_classification import (
    MIN_EFFECTIVE_SUPPORT,
    MIN_TRANSLATION_ACTIVITY,
    RegimeRow,
    build_regime_row,
    classify_r1q,
    robustness_across_cohorts,
    threshold_sensitivity,
    translation_outcomes,
)
from atlas.validation.temporal_kamea import canonical_spec


def _row(
    *,
    body: str = "mars",
    scale: str = "R1-W3D",
    cohort: str = "irregular",
    effective_support: float = 20.0,
    measurable: bool = True,
    saturated: bool = False,
    activity: float = 0.5,
    stationary: float = 0.1,
    merges: int = 40,
) -> RegimeRow:
    """Build a decision-table row with chosen properties."""
    return RegimeRow(
        body=body,
        scale=scale,
        cohort=cohort,
        capacity={
            "effective_support": effective_support,
            "capacity_measurable": measurable,
            "saturated": saturated,
        },
        translation={
            "translation_activity": activity,
            "stationary_fraction": stationary,
        },
        partition={"merges_added_by_right": merges},
        era={},
    )


# ---------------------------------------------------------------------------
# The rule
# ---------------------------------------------------------------------------


def test_evidence_against_r1q_requires_every_condition() -> None:
    """The conjunction is the point: anything less is consistent with R1-Q."""
    assert _row().contradicts_r1q() is True

    # Each condition alone is sufficient to keep the regime consistent.
    assert _row(effective_support=2.0).contradicts_r1q() is False
    assert _row(activity=0.0).contradicts_r1q() is False
    assert _row(merges=0).contradicts_r1q() is False
    assert _row(stationary=0.9).contradicts_r1q() is False
    assert _row(saturated=True).contradicts_r1q() is False
    assert _row(measurable=False).contradicts_r1q() is False


def test_degenerate_regimes_cannot_supply_the_evidence() -> None:
    """The measured mechanism: merges happen where paths are degenerate.

    So a geometry-specific claim has to hold where they are not, or it is
    just restating that small figures coincide.
    """
    degenerate = _row(stationary=0.9, activity=0.9, merges=500)

    assert degenerate.translation_active
    assert degenerate.merges_classes
    assert degenerate.outside_degenerate_paths is False
    assert degenerate.contradicts_r1q() is False


def test_saturated_regimes_cannot_supply_the_evidence() -> None:
    """A saturated sample measures the cohort, not the representation."""
    assert _row(saturated=True, measurable=False).contradicts_r1q() is False


def test_classification_reports_r1q_when_nothing_contradicts() -> None:
    """No contradicting regime means quantization dominance stands."""
    verdict = classify_r1q([_row(activity=0.0), _row(merges=0)])

    assert verdict["r1q_holds"] is True
    assert verdict["classification"].startswith("R1-Q")
    assert verdict["contradicting_regimes"] == []


def test_classification_names_the_contradicting_regime() -> None:
    """A single qualifying regime flips the classification, and is named."""
    verdict = classify_r1q(
        [_row(body="mars", activity=0.0), _row(body="venus")]
    )

    assert verdict["r1q_holds"] is False
    assert verdict["classification"].startswith("R1-G")
    assert verdict["contradicting_regimes"] == ["venus/R1-W3D"]


def test_unstable_activity_cannot_supply_the_evidence() -> None:
    """The stated conjunction includes cross-cohort stability.

    The first implementation checked the per-row clauses only, which would
    have admitted a regime whose activity was a lattice artifact -- exactly
    what the Mercury aliasing result warned about.
    """
    rows = [
        _row(cohort="irregular", activity=0.60),
        _row(cohort="lattice_13d", activity=0.27),
    ]

    verdict = classify_r1q(rows)

    assert verdict["contradicting_regimes"] == []
    assert verdict["rejected_for_instability"] == ["mars/R1-W3D"]
    assert verdict["r1q_holds"] is True
    # The rows still qualified individually; the group did not.
    assert len(verdict["qualifying_rows"]) == 2


def test_stable_activity_across_cohorts_does_supply_evidence() -> None:
    """Agreement across cadences is what makes the evidence credible."""
    rows = [
        _row(cohort="irregular", activity=0.85),
        _row(cohort="lattice_13d", activity=0.87),
        _row(cohort="lattice_47d", activity=0.86),
    ]

    verdict = classify_r1q(rows)

    assert verdict["contradicting_regimes"] == ["mars/R1-W3D"]
    assert verdict["r1q_holds"] is False


def test_a_regime_must_qualify_in_every_cohort() -> None:
    """One passing cohort is not a regime-level result."""
    rows = [
        _row(cohort="irregular", activity=0.85),
        _row(cohort="lattice_13d", activity=0.0),
    ]

    assert classify_r1q(rows)["contradicting_regimes"] == []


def test_thresholds_are_stated_in_the_verdict() -> None:
    """The rule travels with the result, so it cannot be recalled later."""
    verdict = classify_r1q([_row()])

    assert verdict["rule"]["min_effective_support"] == MIN_EFFECTIVE_SUPPORT
    assert verdict["rule"]["min_translation_activity"] == (
        MIN_TRANSLATION_ACTIVITY
    )
    assert "conjunction" in verdict["rule"]


# ---------------------------------------------------------------------------
# Robustness
# ---------------------------------------------------------------------------


def test_activity_that_vanishes_across_cohorts_is_flagged() -> None:
    """Mercury's aliasing showed this is not hypothetical."""
    rows = [
        _row(cohort="irregular", activity=0.8),
        _row(cohort="lattice_13d", activity=0.1),
    ]

    robustness = robustness_across_cohorts(rows)

    assert robustness["stable"] is False
    assert "mars/R1-W3D" in robustness["unstable_across_cohorts"]


def test_consistent_activity_is_not_flagged() -> None:
    """Agreement across cadences is what makes an estimate credible."""
    rows = [
        _row(cohort="irregular", activity=0.80),
        _row(cohort="lattice_13d", activity=0.78),
    ]

    assert robustness_across_cohorts(rows)["stable"] is True


# ---------------------------------------------------------------------------
# Threshold sensitivity
# ---------------------------------------------------------------------------


def test_a_margin_regime_survives_every_threshold() -> None:
    """A regime clearing the cutoffs widely holds across the whole grid.

    This is what separates a threshold-robust finding from a
    threshold-dependent one.
    """
    rows = [
        _row(cohort="irregular", activity=0.85, stationary=0.13),
        _row(cohort="lattice_47d", activity=0.87, stationary=0.13),
    ]

    sensitivity = threshold_sensitivity(rows)

    assert sensitivity["r1g_threshold_robust"] is True
    assert "mars/R1-W3D" in sensitivity["survives_every_threshold"]
    assert sensitivity["threshold_dependent"] == {}


def test_a_borderline_regime_is_flagged_threshold_dependent() -> None:
    """A regime near the stationarity edge survives only some cutoffs."""
    rows = [
        _row(cohort="irregular", activity=0.59, stationary=0.45),
        _row(cohort="lattice_47d", activity=0.60, stationary=0.42),
    ]

    sensitivity = threshold_sensitivity(rows)

    assert "mars/R1-W3D" in sensitivity["threshold_dependent"]
    assert "mars/R1-W3D" not in sensitivity["survives_every_threshold"]


# ---------------------------------------------------------------------------
# The four outcomes stay separate
# ---------------------------------------------------------------------------


def test_the_four_translation_outcomes_are_reported_apart() -> None:
    """Collapsing them has already caused one misreading in this milestone."""
    instants = irregular_cohort(40, seed=3)
    labels = decade_labels(instants)
    encodings = encode_cohort(instants, "mars", canonical_spec("R1-W3D"))

    outcomes = translation_outcomes(encodings, instants, labels)

    assert set(outcomes) >= {
        "signature_changed_fraction",
        "translation_activity",
        "removes_empirical_era_association",
        "changes_blocked_era_predictability",
        "era_association_removed",
        "era_accuracy_change",
    }


def test_a_coarsening_never_increases_era_association() -> None:
    """B2 is a coarsening of B3D, so its mutual information cannot rise."""
    instants = irregular_cohort(60, seed=11)
    labels = decade_labels(instants)

    for key in ("saturn", "mars", "moon"):
        encodings = encode_cohort(instants, key, canonical_spec("R1-W3D"))
        outcomes = translation_outcomes(encodings, instants, labels)

        assert outcomes["era_mi_b2_nats"] <= (
            outcomes["era_mi_b3d_nats"] + 1e-9
        ), key


def test_regime_rows_carry_their_evidence() -> None:
    """A row records what produced its verdict, not only the verdict."""
    instants = irregular_cohort(40, seed=5)
    labels = decade_labels(instants)
    encodings = encode_cohort(instants, "venus", canonical_spec("R1-W3D"))

    row = build_regime_row(
        "venus", "R1-W3D", "irregular", encodings, instants, labels
    )
    payload = row.to_dict()

    assert payload["body"] == "venus"
    assert "capacity" in payload and "partition" in payload
    assert isinstance(payload["contradicts_r1q"], bool)
