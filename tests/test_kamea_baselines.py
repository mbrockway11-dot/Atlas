"""Tests for the B0-B3 baseline framework.

The audit's whole value rests on the four encodings differing in nothing but
the arrangement and the reduction. These tests pin that, and pin the
estimators that keep a saturated sample from being read as a measurement of
capacity.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from atlas.validation.kamea_baselines import (
    COPRIME_CADENCE_DAYS,
    ENCODINGS,
    audit_body,
    bijection_check,
    cadence_cohorts,
    compression_profile,
    encode_baselines,
    encode_cohort,
    irregular_cohort,
    occupancy_estimates,
    regular_cohort,
    shannon_entropy,
)
from atlas.validation.temporal_kamea import build_trajectory, canonical_spec


INSTANT = datetime(1994, 7, 16, 20, 13, 11, tzinfo=UTC)
SPEC = canonical_spec("R1-W3D")


# ---------------------------------------------------------------------------
# Matching -- the audit is worthless without it
# ---------------------------------------------------------------------------


def test_all_encodings_come_from_one_trajectory() -> None:
    """Sharing a trajectory is what guarantees matched inputs."""
    trajectory = build_trajectory(INSTANT, "mars", SPEC)
    encoded = encode_baselines(trajectory)

    assert set(encoded) == set(ENCODINGS)
    assert encoded["B1"] == trajectory.coordinates
    assert encoded["B3"] == trajectory.values
    assert encoded["B2"] == trajectory.core_shape
    assert len(encoded["B0"]) == 1


def test_b0_is_the_centre_cell() -> None:
    """B0 is the cell at the instant itself, not an endpoint."""
    trajectory = build_trajectory(INSTANT, "venus", SPEC)
    encoded = encode_baselines(trajectory)

    centre = len(trajectory.coordinates) // 2

    assert encoded["B0"] == (trajectory.coordinates[centre],)
    assert trajectory.instants[centre] == INSTANT


def test_b3_withholds_only_the_square_lookup() -> None:
    """B3 shares B1's bins, length and cardinality -- not its arrangement."""
    trajectory = build_trajectory(INSTANT, "mars", SPEC)
    encoded = encode_baselines(trajectory)

    assert len(encoded["B3"]) == len(encoded["B1"])
    assert encoded["B3"] == trajectory.path.raw_values


def test_b1_and_b3_are_informationally_identical() -> None:
    """Cell lookup is a bijection, so these cannot differ in information.

    A structural check on the harness rather than a finding. It also locates
    the real comparison: B2 against B3 is the only one where the reduction
    can show an information effect.
    """
    instants = regular_cohort(29, 40)
    encodings = encode_cohort(instants, "mercury", SPEC)

    check = bijection_check(encodings)

    assert check["distinct_b1"] == check["distinct_b3"]
    assert check["entropy_b1"] == pytest.approx(check["entropy_b3"])
    assert check["collision_structure_matches"] is True


# ---------------------------------------------------------------------------
# Occupancy estimators
# ---------------------------------------------------------------------------


def test_saturated_samples_are_flagged_not_reported_as_capacity() -> None:
    """All-singleton samples measure the cohort, not the representation."""
    estimates = occupancy_estimates(list(range(50)))

    assert estimates["saturated"] is True
    assert estimates["capacity_measurable"] is False
    assert estimates["singleton_fraction"] == 1.0
    assert estimates["good_turing_coverage"] == 0.0
    assert estimates["estimated_unseen_mass"] == 1.0


def test_a_concentrated_sample_is_measurable() -> None:
    """A distribution with repeats supports a capacity claim."""
    estimates = occupancy_estimates(["a"] * 40 + ["b"] * 30 + ["c"] * 30)

    assert estimates["saturated"] is False
    assert estimates["capacity_measurable"] is True
    assert estimates["observed_signatures"] == 3
    assert estimates["good_turing_coverage"] == 1.0
    assert 2.0 < estimates["effective_support"] <= 3.0


def test_chao1_estimates_richness_beyond_the_sample() -> None:
    """Unobserved signatures are estimated, not assumed absent."""
    with_rares = occupancy_estimates(["a"] * 20 + ["b"] * 10 + ["c", "d"])

    assert with_rares["observed_signatures"] == 4
    assert with_rares["chao1_lower_bound"] > 4


def test_entropy_of_a_constant_is_zero() -> None:
    """A stationary body carries no information, and the number says so."""
    assert shannon_entropy(["x"] * 25) == pytest.approx(0.0)
    assert occupancy_estimates(["x"] * 25)["effective_support"] == (
        pytest.approx(1.0)
    )


def test_empty_samples_do_not_raise() -> None:
    """A batch continues past a body that produced nothing."""
    assert occupancy_estimates([])["observed_signatures"] == 0
    assert shannon_entropy([]) == 0.0


# ---------------------------------------------------------------------------
# Compression
# ---------------------------------------------------------------------------


def test_reduction_creates_equivalence_classes() -> None:
    """Many distinct paths collapse into one shape.

    Reported as retention rather than loss: a reduction is supposed to lose
    information, so lower entropy is not itself a defect. What matters is
    the equivalence structure created.
    """
    encodings = encode_cohort(regular_cohort(13, 60), "mars", SPEC)
    profile = compression_profile(encodings)

    assert profile["distinct_shapes"] <= profile["distinct_paths"]
    assert profile["many_to_one_ratio"] >= 1.0
    assert 0.0 <= profile["entropy_retained"] <= 1.0
    assert profile["entropy_b2_nats"] <= profile["entropy_b1_nats"]


# ---------------------------------------------------------------------------
# Cohorts
# ---------------------------------------------------------------------------


def test_irregular_cohorts_are_deterministic_and_unlatticed() -> None:
    """Reproducible from a frozen seed, without a fixed spacing."""
    first = irregular_cohort(40, seed=7)
    second = irregular_cohort(40, seed=7)

    assert first == second
    assert first != irregular_cohort(40, seed=8)
    assert first == sorted(first)

    gaps = {
        (later - earlier).total_seconds()
        for earlier, later in zip(first, first[1:])
    }

    # A lattice would produce one gap; an irregular draw produces many.
    assert len(gaps) > len(first) // 2


def test_cadences_are_coprime() -> None:
    """Coprime lattices cannot share an aliasing period.

    A single regular cadence can beat against a body's period, so agreement
    across coprime lattices is what makes an occupancy estimate credible.
    """
    from math import gcd

    for index, left in enumerate(COPRIME_CADENCE_DAYS):
        for right in COPRIME_CADENCE_DAYS[index + 1 :]:
            assert gcd(left, right) == 1


def test_cadence_cohorts_cover_irregular_and_lattices() -> None:
    """The audit always has an unlatticed cohort to compare against."""
    cohorts = cadence_cohorts(30, seed=11)

    assert cohorts[0].kind == "deterministic_irregular"
    assert len(cohorts) == 1 + len(COPRIME_CADENCE_DAYS)
    assert all(len(cohort.instants) == 30 for cohort in cohorts)


# ---------------------------------------------------------------------------
# End to end
# ---------------------------------------------------------------------------


def test_audit_body_reports_capacity_stability_and_compression() -> None:
    """Capacity is never reported alone.

    A maximally discriminative encoding may simply respond to every
    incidental detail, so the three must be readable against each other.
    """
    cohort = cadence_cohorts(24, seed=3)[0]
    result = audit_body(cohort, "venus", SPEC)

    assert set(result["capacity"]) == set(ENCODINGS)
    assert set(result["stability"]) == set(ENCODINGS)
    assert result["bijection_check"]["collision_structure_matches"] is True
    assert 0.0 <= result["stability"]["B2"] <= 1.0


def test_stationary_bodies_have_minimal_capacity() -> None:
    """Saturn at the shortest scale is nearly a constant, and reads as one."""
    cohort = cadence_cohorts(24, seed=3)[0]
    result = audit_body(cohort, "saturn", SPEC)

    assert result["capacity"]["B2"]["effective_support"] < 3.0
    assert result["stability"]["B2"] == 1.0
