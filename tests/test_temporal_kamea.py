"""Tests for temporal Kamea trajectories (Temporal 1C's R1).

The representation exists because pointwise cell locality was measured to be
unobtainable (`test_kamea_locality.py`) and because simultaneous planetary
positions supply no ordering for a path processor. These tests pin the two
properties that replaced those: time supplies the order, and stability is
asserted at the path level rather than the cell level.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from atlas.kamea.squares import KAMEAS
from atlas.validation.temporal_kamea import (
    CANONICAL_FAMILY,
    CANONICAL_SCALES,
    CLASSICAL_BODIES,
    MEAN_DAILY_MOTION,
    UNSUPPORTED_BODIES,
    SamplingFamily,
    TemporalKameaPath,
    TrajectoryError,
    TrajectorySpec,
    build_all_trajectories,
    build_trajectory,
    canonical_spec,
    path_similarity,
    quantization_bin_degrees,
    quantize_longitude,
    sample_instants,
    traversal_requirements,
    window_to_traverse,
)


INSTANT = datetime(1994, 7, 16, 20, 13, 11, tzinfo=UTC)

FIXED = TrajectorySpec(
    family=SamplingFamily.FIXED_TIME, half_width=4, step=timedelta(hours=6)
)


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------


def test_scope_is_the_classical_seven() -> None:
    """R1 covers exactly the bodies that have a traditional square."""
    assert set(CLASSICAL_BODIES) == set(KAMEAS)
    assert len(CLASSICAL_BODIES) == 7
    assert set(MEAN_DAILY_MOTION) == set(CLASSICAL_BODIES)


def test_modern_bodies_are_refused_explicitly() -> None:
    """Uranus, Neptune and Pluto raise rather than silently vanishing.

    An omission that is not written down is indistinguishable from a bug,
    and R0 carries all ten bodies, so the gap must be visible at the call.
    """
    for body in UNSUPPORTED_BODIES:
        with pytest.raises(TrajectoryError, match="classical seven"):
            build_trajectory(INSTANT, body.lower(), FIXED)


def test_all_trajectories_are_independent_per_square() -> None:
    """Each body is projected only onto its own Kamea.

    Planet-locality holds by construction: Mars is never ordered relative to
    Venus, so no cross-body coupling can enter the geometry.
    """
    trajectories = build_all_trajectories(INSTANT, FIXED)

    assert set(trajectories) == set(CLASSICAL_BODIES)

    for key, trajectory in trajectories.items():
        square = KAMEAS[key]

        assert trajectory.kamea_key == key
        assert all(
            1 <= value <= square.max_value
            for value in trajectory.path.reduced_values
        )
        assert all(
            0 <= row < square.size and 0 <= column < square.size
            for row, column in trajectory.coordinates
        )


# ---------------------------------------------------------------------------
# Ordering -- the gap that made the original 1C framing unanswerable
# ---------------------------------------------------------------------------


def test_samples_are_chronological_and_centered() -> None:
    """Time supplies the ordering, and the window brackets the instant."""
    instants = sample_instants(INSTANT, "mars", FIXED)

    assert len(instants) == 2 * FIXED.half_width + 1
    assert list(instants) == sorted(instants)
    assert instants[len(instants) // 2] == INSTANT
    assert instants[0] < INSTANT < instants[-1]


def test_trailing_window_ends_at_the_instant() -> None:
    """A non-centered window is past-only, for a causal study to opt into.

    Not the default: a trailing window imposes a causal reading that suits
    neither births nor historical events.
    """
    trailing = TrajectorySpec(
        family=SamplingFamily.FIXED_TIME, half_width=4, centered=False
    )
    instants = sample_instants(INSTANT, "mars", trailing)

    assert instants[-1] == INSTANT
    assert all(moment <= INSTANT for moment in instants)


def test_a_single_point_is_not_a_path() -> None:
    """A trajectory needs samples either side; one cell has no geometry."""
    with pytest.raises(TrajectoryError, match="not a path"):
        TrajectorySpec(
            family=SamplingFamily.FIXED_TIME, half_width=0
        ).sample_offsets()


# ---------------------------------------------------------------------------
# Quantization
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", sorted(CLASSICAL_BODIES))
def test_quantizer_covers_the_whole_square(key: str) -> None:
    """Every cell is reachable, and nothing escapes the range."""
    square = KAMEAS[key]
    produced = {
        quantize_longitude(degree * 0.1, key) for degree in range(3600)
    }

    assert produced == set(range(1, square.max_value + 1))


@pytest.mark.parametrize("key", sorted(CLASSICAL_BODIES))
def test_quantizer_handles_the_wrap(key: str) -> None:
    """The 360 boundary is a wrap, not an out-of-range cell."""
    square = KAMEAS[key]

    assert quantize_longitude(0.0, key) == 1
    assert quantize_longitude(360.0, key) == 1
    assert quantize_longitude(-0.001, key) == square.max_value
    assert quantize_longitude(359.9999, key) == square.max_value


def test_bin_width_follows_square_size() -> None:
    """Resolution differs per body by design, following the tradition."""
    assert quantization_bin_degrees("saturn") == pytest.approx(40.0)
    assert quantization_bin_degrees("moon") == pytest.approx(360.0 / 81)
    assert quantization_bin_degrees("saturn") > quantization_bin_degrees(
        "moon"
    )


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_trajectories_are_deterministic() -> None:
    """The same instant always produces the same path."""
    first = build_trajectory(INSTANT, "venus", FIXED)
    second = build_trajectory(INSTANT, "venus", FIXED)

    assert first.values == second.values
    assert first.coordinates == second.coordinates
    assert first.core_geometry == second.core_geometry


def test_naive_instants_are_refused() -> None:
    """A naive datetime would shift every position by the machine offset."""
    with pytest.raises(Exception, match="timezone-aware"):
        build_trajectory(datetime(1994, 7, 16, 20, 13), "venus", FIXED)


def test_spec_hash_separates_representations() -> None:
    """A path built under different parameters is a different object."""
    other = TrajectorySpec(
        family=SamplingFamily.FIXED_TIME, half_width=5, step=timedelta(hours=6)
    )
    relative = TrajectorySpec(family=SamplingFamily.BODY_RELATIVE)

    assert FIXED.spec_hash() != other.spec_hash()
    assert FIXED.spec_hash() != relative.spec_hash()
    assert FIXED.spec_hash() == TrajectorySpec(
        family=SamplingFamily.FIXED_TIME,
        half_width=4,
        step=timedelta(hours=6),
    ).spec_hash()


# ---------------------------------------------------------------------------
# Path stability -- the invariant that replaced pointwise continuity
# ---------------------------------------------------------------------------


def test_identical_trajectories_are_perfectly_similar() -> None:
    """All four levels agree when nothing changed."""
    trajectory = build_trajectory(INSTANT, "mars", FIXED)
    similarity = path_similarity(trajectory, trajectory)

    assert similarity == {
        "raw_sequence": 1.0,
        "projected_path": 1.0,
        "reduced_occupancy": 1.0,
        "core_geometry": 1.0,
    }


def test_one_minute_shifts_preserve_the_path() -> None:
    """The primary acceptance criterion, at the precision cohorts admit.

    The USGS catalogue carries SECOND and MINUTE precision, so a
    representation that moves under a one-minute shift would track rounding
    rather than the sky.
    """
    for key in sorted(CLASSICAL_BODIES):
        reference = build_trajectory(INSTANT, key, FIXED)
        shifted = build_trajectory(INSTANT + timedelta(minutes=1), key, FIXED)

        assert path_similarity(reference, shifted)["projected_path"] >= 0.9


def test_cross_square_comparison_is_refused() -> None:
    """Two bodies' paths live on different squares and are incomparable."""
    mars = build_trajectory(INSTANT, "mars", FIXED)
    venus = build_trajectory(INSTANT, "venus", FIXED)

    with pytest.raises(TrajectoryError, match="different squares"):
        path_similarity(mars, venus)


# ---------------------------------------------------------------------------
# The locality-versus-window tension
# ---------------------------------------------------------------------------


def test_slow_bodies_cannot_traverse_a_local_window() -> None:
    """Saturn needs years to leave its starting cell.

    Structural, not a tuning failure: the tradition pairs the slowest body
    with the coarsest square, so no window short enough to describe an
    instant gives Saturn a moving path. This is the finding that stopped 1C
    from being closed by parameter choice.
    """
    assert window_to_traverse("saturn") > timedelta(days=3 * 365)
    assert window_to_traverse("moon") < timedelta(days=1)

    requirements = traversal_requirements()
    ordered = sorted(requirements, key=lambda k: requirements[k]["days_per_cell"])

    assert ordered[0] == "moon"
    assert ordered[-1] == "saturn"


def test_bin_relative_sampling_scales_the_step_to_the_square() -> None:
    """The third family steps by a fraction of each body's own bin."""
    spec = TrajectorySpec(
        family=SamplingFamily.BIN_RELATIVE, half_width=4, bin_fraction=0.5
    )

    for key in sorted(CLASSICAL_BODIES):
        expected = window_to_traverse(key, 0.5)

        assert spec.step_for(key) == expected

    # Which buys traversal at the cost of window length: Saturn's window
    # spans years, so its "instant" is an era.
    assert spec.step_for("saturn") > spec.step_for("moon") * 1000


# ---------------------------------------------------------------------------
# Retrograde motion, read off the path rather than flagged
# ---------------------------------------------------------------------------


def _synthetic(longitudes: tuple[float, ...]) -> TemporalKameaPath:
    """Build a trajectory from chosen longitudes, bypassing the ephemeris."""
    values = tuple(quantize_longitude(v, "mars") for v in longitudes)

    return TemporalKameaPath(
        kamea_key="mars",
        body="Mars",
        spec=FIXED,
        instants=tuple(
            INSTANT + timedelta(hours=6 * i) for i in range(len(longitudes))
        ),
        longitudes=longitudes,
        values=values,
        path=KAMEAS["mars"].project_values(list(values)),
    )


def test_canonical_r1_shares_one_window_across_bodies() -> None:
    """Contemporaneity is what makes R1 canonical.

    Per-body windows solve cell occupancy by changing the meaning of the
    object: a Moon path over two days beside a Saturn path over twenty years
    is not an observation of the same temporal neighbourhood.
    """
    spec = canonical_spec("R1-W30D")

    assert spec.canonical
    assert spec.family is CANONICAL_FAMILY

    steps = {spec.step_for(key) for key in CLASSICAL_BODIES}

    assert len(steps) == 1

    instants = {
        key: sample_instants(INSTANT, key, spec) for key in CLASSICAL_BODIES
    }

    assert len({value for value in instants.values()}) == 1


@pytest.mark.parametrize("scale", sorted(CANONICAL_SCALES))
def test_each_scale_is_a_separately_hashed_representation(
    scale: str,
) -> None:
    """R1-W3D and R1-W1Y are different objects, not the same one tuned."""
    spec = canonical_spec(scale)
    others = {
        canonical_spec(other).spec_hash()
        for other in CANONICAL_SCALES
        if other != scale
    }

    assert spec.canonical
    assert spec.spec_hash() not in others

    span = spec.step * spec.half_width * 2

    assert span == CANONICAL_SCALES[scale] * 2


def test_body_relative_families_are_not_canonical() -> None:
    """They remain available as contrasts, and cannot pass as canonical."""
    for family in (SamplingFamily.BODY_RELATIVE, SamplingFamily.BIN_RELATIVE):
        assert not TrajectorySpec(family=family, scale="R1-W3D").canonical

    # A trailing window is not canonical either: it imposes a causal reading.
    assert not TrajectorySpec(
        family=CANONICAL_FAMILY, scale="R1-W3D", centered=False
    ).canonical


def test_unknown_scale_is_refused() -> None:
    """A canonical spec cannot be built for an unnamed scale."""
    with pytest.raises(TrajectoryError, match="not a canonical scale"):
        canonical_spec("R1-W7D")


def test_stationary_slow_bodies_are_reported_honestly() -> None:
    """Saturn is static at the shortest scale, and says so.

    The frozen 1C decision: degeneracy is a property of the representation's
    temporal resolution, so it must be visible in the output rather than
    dropped or expanded away.
    """
    saturn = build_trajectory(INSTANT, "saturn", canonical_spec("R1-W3D"))
    diagnostics = saturn.diagnostics()

    assert diagnostics["stationary"] is True
    assert diagnostics["distinct_cells"] == 1
    assert diagnostics["transition_count"] == 0
    assert diagnostics["path_distance"] == 0
    assert diagnostics["longest_stationary_run"] == len(saturn.coordinates)

    moon = build_trajectory(INSTANT, "moon", canonical_spec("R1-W3D"))

    assert moon.diagnostics()["stationary"] is False
    assert moon.diagnostics()["transition_count"] > 0


def test_diagnostics_report_every_required_field() -> None:
    """The reportable set is fixed, so an R1 study cannot omit one."""
    diagnostics = build_trajectory(INSTANT, "venus").diagnostics()

    assert set(diagnostics) >= {
        "distinct_cells",
        "transition_count",
        "occupancy_fraction",
        "longest_stationary_run",
        "reversal_count",
        "path_distance",
        "reduced_path_length",
        "core_shape",
        "stationary",
    }


def test_core_shape_normalizes_to_its_own_origin() -> None:
    """The shape records offsets from the first visited cell."""
    trajectory = _synthetic((10.0, 25.0, 40.0))

    geometry = trajectory.core_geometry
    shape = trajectory.core_shape

    assert shape[0] == (0, 0)
    assert len(shape) == len(geometry)
    assert shape == tuple(
        (row - geometry[0][0], column - geometry[0][1])
        for row, column in geometry
    )


def test_longitude_translation_is_not_grid_translation() -> None:
    """Shifting every longitude by one bin does not shift the figure.

    A one-bin shift adds one to every value, and the square scatters
    consecutive values by construction, so the path lands somewhere
    unrelated. Recorded because it is the locality finding reappearing at
    the shape level: core_shape is invariant to where a figure sits on the
    grid, but nothing makes it invariant to a shift in longitude.
    """
    bin_width = quantization_bin_degrees("mars")

    first = _synthetic((10.0, 25.0, 40.0))
    shifted = _synthetic(
        (10.0 + bin_width, 25.0 + bin_width, 40.0 + bin_width)
    )

    assert shifted.values == tuple(value + 1 for value in first.values)
    assert first.core_shape != shifted.core_shape


def test_direct_motion_has_no_reversals() -> None:
    """A monotone trajectory reverses nowhere."""
    assert _synthetic((10.0, 11.0, 12.0, 13.0)).reversals == 0


def test_retrograde_motion_shows_as_a_reversal() -> None:
    """Direction change is already in the trajectory.

    So no separate retrograde flag is added: it would duplicate information
    the path carries, unless 1D shows the geometry loses it.
    """
    assert _synthetic((10.0, 11.0, 10.5, 9.0)).reversals == 1
    assert _synthetic((10.0, 9.0, 10.0, 9.0)).reversals == 2


def test_angular_span_unwraps_the_boundary() -> None:
    """Motion across 360 degrees is two degrees, not 358."""
    span = _synthetic((359.0, 0.0, 1.0)).angular_span_degrees

    assert span == pytest.approx(2.0)
