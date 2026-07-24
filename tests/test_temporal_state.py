"""Tests for deterministic temporal state vectors.

The temporal branch's entire value rests on reproducibility, so the checks
that would catch a regression live here rather than only in the milestone
script. In particular: a naive datetime must be refused, because silently
treating local time as UTC would make every result depend on the machine's
time zone.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import numpy as np
import pytest

from atlas.validation.temporal_state import (
    ORDERED_BODIES,
    ORDERED_QUANTITIES,
    ordered_body_pairs,
    TemporalStateError,
    build_temporal_matrix,
    build_temporal_state,
    matched_date_controls,
    require_utc,
    temporal_feature_layout,
    temporal_schema_hash,
    verify_determinism,
)


TOHOKU = datetime(2011, 3, 11, 5, 46, 24, tzinfo=UTC)
APOLLO = datetime(1969, 7, 20, 20, 17, 40, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


def test_schema_hash_is_deterministic() -> None:
    """The same schema yields the same hash on every call."""
    assert temporal_schema_hash() == temporal_schema_hash()
    assert len(temporal_schema_hash()) == 64


def test_layout_covers_per_body_and_pairwise_features() -> None:
    """Layout is per-body quantities plus every unordered body pair.

    Pairwise angular separations belong to the *raw* representation:
    relative geometry is available directly from the coordinates, so
    omitting it would make the raw baseline artificially weak in any later
    comparison against a derived representation.
    """
    layout = temporal_feature_layout()
    pairs = ordered_body_pairs()

    expected = (
        len(ORDERED_BODIES) * len(ORDERED_QUANTITIES) + len(pairs) * 2
    )

    assert len(layout) == expected
    assert len(set(layout)) == len(layout)
    assert layout[0].startswith(ORDERED_BODIES[0])
    assert len(pairs) == len(ORDERED_BODIES) * (len(ORDERED_BODIES) - 1) // 2
    assert any("separation_cos" in label for label in layout)


# ---------------------------------------------------------------------------
# Explicit instants
# ---------------------------------------------------------------------------


def test_naive_datetime_is_refused() -> None:
    """A naive datetime would be read differently in different time zones."""
    with pytest.raises(TemporalStateError, match="timezone-aware"):
        build_temporal_state(datetime(2011, 3, 11, 5, 46))


def test_non_utc_instants_are_converted_not_rejected() -> None:
    """An aware non-UTC instant is converted, and agrees with its UTC twin."""
    tokyo = timezone(timedelta(hours=9))
    same_moment = TOHOKU.astimezone(tokyo)

    assert require_utc(same_moment) == TOHOKU
    assert (
        build_temporal_state(same_moment).content_hash()
        == build_temporal_state(TOHOKU).content_hash()
    )


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_repeated_builds_are_identical() -> None:
    """The same instant compiles to the same state every time."""
    first = build_temporal_state(TOHOKU)
    second = build_temporal_state(TOHOKU)

    assert first.content_hash() == second.content_hash()
    assert np.array_equal(first.as_array(), second.as_array())


def test_distinct_instants_produce_distinct_states() -> None:
    """Different moments must not silently collapse to the same state."""
    assert (
        build_temporal_state(TOHOKU).values_hash()
        != build_temporal_state(APOLLO).values_hash()
    )


def test_sub_minute_precision_is_preserved() -> None:
    """Seconds must reach the ephemeris.

    The builder originally formatted the instant as HH:MM, silently
    quantizing every state to the minute. Event catalogues record seconds,
    so two quakes 40 seconds apart would have been indistinguishable.
    """
    early = build_temporal_state(
        datetime(2011, 3, 11, 5, 46, 10, tzinfo=UTC)
    )
    late = build_temporal_state(
        datetime(2011, 3, 11, 5, 46, 50, tzinfo=UTC)
    )

    assert early.julian_day != late.julian_day
    assert early.values_hash() != late.values_hash()


def test_values_hash_excludes_the_instant() -> None:
    """Collision detection needs a hash over values alone.

    content_hash includes the instant, so every state is unique by
    construction under it -- a collision could never be found. values_hash
    is what makes the question answerable.
    """
    state = build_temporal_state(TOHOKU)

    assert state.values_hash() != state.content_hash()
    assert TOHOKU.isoformat() not in state.values_hash()


def test_verify_determinism_reports_stability() -> None:
    """The milestone check reports cleanly on a stable set."""
    result = verify_determinism([TOHOKU, APOLLO], repeats=3)

    assert result["all_stable"] is True
    assert result["unstable"] == []
    assert result["instants"] == 2


def test_state_records_engine_and_schema() -> None:
    """Provenance travels with the state."""
    state = build_temporal_state(TOHOKU)

    assert state.ephemeris_engine_version
    assert state.schema_hash == temporal_schema_hash()
    assert state.julian_day > 0
    assert len(state.values) == len(temporal_feature_layout())


# ---------------------------------------------------------------------------
# Encoding choices
# ---------------------------------------------------------------------------


def test_longitude_is_encoded_as_cosine_and_sine() -> None:
    """Angles wrap, so a raw degree value would misplace 359 and 1.

    The (cos, sin) pair keeps nearby angles nearby, which a bare degree
    column would not.
    """
    state = build_temporal_state(TOHOKU)
    layout = list(state.layout)

    cos_index = layout.index("Sun|longitude_cos")
    sin_index = layout.index("Sun|longitude_sin")

    cosine = state.values[cos_index]
    sine = state.values[sin_index]

    assert -1.0 <= cosine <= 1.0
    assert -1.0 <= sine <= 1.0
    assert cosine**2 + sine**2 == pytest.approx(1.0)


def test_retrograde_is_encoded_as_a_flag() -> None:
    """Retrograde is boolean and encoded as 0.0 or 1.0."""
    state = build_temporal_state(TOHOKU)
    layout = list(state.layout)

    for body in ORDERED_BODIES:
        value = state.values[layout.index(f"{body}|retrograde")]
        assert value in (0.0, 1.0)


def test_matrix_rows_align_with_instants() -> None:
    """The matrix builder preserves order and width."""
    matrix, states = build_temporal_matrix([TOHOKU, APOLLO])

    assert matrix.shape == (2, len(temporal_feature_layout()))
    assert states[0].instant == TOHOKU
    assert np.array_equal(matrix[1], states[1].as_array())


def test_empty_instant_list_returns_empty_matrix() -> None:
    """No instants is a valid, non-crashing input."""
    matrix, states = build_temporal_matrix([])

    assert matrix.shape[0] == 0
    assert states == []


# ---------------------------------------------------------------------------
# Matched controls
# ---------------------------------------------------------------------------


def test_controls_respect_the_minimum_offset() -> None:
    """A control must not be effectively the same sky as the event."""
    controls = matched_date_controls(
        TOHOKU, count=20, minimum_offset_days=90, seed=3
    )

    for control in controls:
        assert abs((control - TOHOKU).days) >= 90


def test_controls_are_drawn_on_both_sides() -> None:
    """Controls carry no net direction in time."""
    controls = matched_date_controls(TOHOKU, count=20, seed=3)

    before = sum(1 for c in controls if c < TOHOKU)
    after = sum(1 for c in controls if c > TOHOKU)

    assert before > 0
    assert after > 0


def test_controls_are_deterministic() -> None:
    """The same seed yields the same controls."""
    assert matched_date_controls(TOHOKU, count=8, seed=11) == (
        matched_date_controls(TOHOKU, count=8, seed=11)
    )


def test_controls_reject_an_inverted_offset_range() -> None:
    """A minimum above the maximum is a configuration error."""
    with pytest.raises(TemporalStateError, match="minimum_offset_days"):
        matched_date_controls(
            TOHOKU, minimum_offset_days=500, maximum_offset_days=100
        )


# ---------------------------------------------------------------------------
# Independence from the identity branch
# ---------------------------------------------------------------------------


def test_temporal_state_needs_no_identity_input() -> None:
    """A temporal state is a function of an instant alone.

    The branches are deliberately independent: nothing here consumes a name,
    a profile, or an identity vector.
    """
    import inspect

    source = inspect.getsource(build_temporal_state)

    for identity_term in ("profile", "identity_vector", "cipher"):
        assert identity_term not in source
