"""Tests for temporal control generators and era diagnostics.

The centrepiece is a negative control: synthetic "events" drawn from a narrow
era, compared against deliberately out-of-era controls. A flawed generator
manufactures a large apparent effect from era structure alone, and a
window-confined one does not.

That test exists because Temporal 2 v1 produced exactly that artifact --
p=0.0005 with d=-0.365 from a control family sampling 35.7% outside the event
window -- and nothing in the harness caught it before the results were read.
It is a regression test for every future control implementation.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from atlas.validation.temporal_controls import (
    CONTROL_FAMILIES,
    ControlGenerationError,
    ObservationWindow,
    era_balance,
    era_stratified_controls,
    feature_imbalance,
    matched_controls,
    nearby_controls,
    symmetric_shift_controls,
    window_from_events,
    window_random_controls,
)
from atlas.validation.temporal_state import (
    build_temporal_matrix,
    temporal_feature_layout,
)


WINDOW = ObservationWindow(
    earliest=datetime(1970, 1, 1, tzinfo=UTC),
    latest=datetime(2025, 12, 31, tzinfo=UTC),
)


def _events(count: int = 40, seed: int = 3) -> list[datetime]:
    """Return synthetic events spread across the window."""
    rng = np.random.default_rng(seed)

    return [
        WINDOW.earliest
        + timedelta(seconds=int(rng.integers(0, WINDOW.span_seconds)))
        for _ in range(count)
    ]


# ---------------------------------------------------------------------------
# Window confinement
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("family", sorted(CONTROL_FAMILIES))
def test_every_family_stays_inside_the_window(family: str) -> None:
    """No v2 generator may emit a control outside the observation window.

    This is the single property whose absence produced v1's spurious result.
    """
    generator = CONTROL_FAMILIES[family]
    rng = np.random.default_rng(11)

    for event in _events(count=25):
        for control in generator(
            event, count=10, window=WINDOW, rng=rng
        ):
            assert WINDOW.contains(control), (family, control)


def test_matched_controls_near_a_boundary_still_produce_draws() -> None:
    """An event at the window edge must still get controls.

    Rejection sampling could starve here if the sign never flipped, leaving
    edge events silently under-controlled.
    """
    edge = WINDOW.earliest + timedelta(days=200)
    controls = matched_controls(
        edge, count=10, window=WINDOW, rng=np.random.default_rng(5)
    )

    assert len(controls) >= 8
    assert all(WINDOW.contains(c) for c in controls)


def test_symmetric_shift_is_two_sided() -> None:
    """v1 shifted forward only, which biased its era. v2 must not."""
    event = datetime(1998, 6, 1, tzinfo=UTC)
    controls = symmetric_shift_controls(
        event, count=60, window=WINDOW, rng=np.random.default_rng(7)
    )

    assert any(c < event for c in controls)
    assert any(c > event for c in controls)


def test_era_stratified_controls_stay_in_band() -> None:
    """The strictest family holds slow-planet state nearly fixed."""
    event = datetime(2000, 1, 1, tzinfo=UTC)
    controls = era_stratified_controls(
        event,
        count=40,
        window=WINDOW,
        rng=np.random.default_rng(9),
        era_band_years=2,
    )

    for control in controls:
        assert abs((control - event).days) <= 2 * 366


def test_nearby_controls_respect_their_day_bounds() -> None:
    """The one family carried over from v1 unchanged."""
    event = datetime(2005, 5, 5, tzinfo=UTC)
    controls = nearby_controls(
        event, count=40, window=WINDOW, rng=np.random.default_rng(2)
    )

    for control in controls:
        assert 3 <= abs((control - event).days) <= 30


def test_window_from_events_requires_events() -> None:
    """An empty cohort has no window."""
    with pytest.raises(ControlGenerationError):
        window_from_events([])


# ---------------------------------------------------------------------------
# Era balance diagnostics
# ---------------------------------------------------------------------------


def test_era_balance_detects_out_of_window_controls() -> None:
    """The diagnostic must catch what v1's design did."""
    events = _events()
    bad = [event + timedelta(days=40 * 365) for event in events]

    balance = era_balance(events, bad, WINDOW)

    assert balance["fraction_outside_event_window"] > 0.5
    assert balance["mean_absolute_year_difference"] > 30


def test_era_balance_is_near_zero_for_confined_controls() -> None:
    """A window-confined family reports no imbalance."""
    events = _events()
    rng = np.random.default_rng(4)
    good = [
        control
        for event in events
        for control in window_random_controls(
            event, count=5, window=WINDOW, rng=rng
        )
    ]

    balance = era_balance(events, good, WINDOW)

    assert balance["fraction_outside_event_window"] == 0.0


def test_feature_imbalance_ranking_survives_serialization() -> None:
    """Body ranking is a list, not a dict.

    A dict's order does not survive JSON serialization with sort_keys=True,
    which once silently turned an imbalance ranking into an alphabetical one
    and made a mechanism check report the opposite of the truth.
    """
    layout = temporal_feature_layout()
    rng = np.random.default_rng(1)

    events = rng.random((20, len(layout)))
    controls = rng.random((20, len(layout))) + 0.5

    result = feature_imbalance(events, controls, layout)

    assert isinstance(result["body_ranking"], list)
    values = [
        row["mean_absolute_standardized_difference"]
        for row in result["body_ranking"]
    ]
    assert values == sorted(values, reverse=True)


# ---------------------------------------------------------------------------
# The negative control
# ---------------------------------------------------------------------------


def test_out_of_era_controls_manufacture_a_large_apparent_effect() -> None:
    """A flawed generator produces a big effect from era structure alone.

    Synthetic "events" from 1970-1980 against controls from 2010-2020. The
    event labels carry no meaning whatsoever, so any separation is era
    leakage. If this test stops finding an effect, the diagnostic below is
    no longer proving anything.
    """
    rng = np.random.default_rng(13)
    span = int((datetime(1980, 1, 1, tzinfo=UTC)
                - datetime(1970, 1, 1, tzinfo=UTC)).total_seconds())

    events = [
        datetime(1970, 1, 1, tzinfo=UTC)
        + timedelta(seconds=int(rng.integers(0, span)))
        for _ in range(40)
    ]
    out_of_era = [
        datetime(2010, 1, 1, tzinfo=UTC)
        + timedelta(seconds=int(rng.integers(0, span)))
        for _ in range(200)
    ]

    layout = temporal_feature_layout()
    event_matrix, _ = build_temporal_matrix(events)
    control_matrix, _ = build_temporal_matrix(out_of_era)

    imbalance = feature_imbalance(event_matrix, control_matrix, layout)

    # Era leakage is large and lands on the slow bodies.
    assert imbalance["max_absolute_standardized_difference"] > 1.0

    top_features = " ".join(
        row["feature"] for row in imbalance["features"][:6]
    )
    assert any(
        body in top_features for body in ("Uranus", "Neptune", "Pluto")
    )


def test_window_confined_controls_remove_the_manufactured_effect() -> None:
    """The v2 generators eliminate what the flawed design created.

    Same synthetic events, but controls drawn from the events' own era.
    Imbalance must drop by a wide margin.
    """
    rng = np.random.default_rng(13)
    window = ObservationWindow(
        earliest=datetime(1970, 1, 1, tzinfo=UTC),
        latest=datetime(1980, 1, 1, tzinfo=UTC),
    )
    span = window.span_seconds

    events = [
        window.earliest + timedelta(seconds=int(rng.integers(0, span)))
        for _ in range(40)
    ]

    confined = [
        control
        for event in events
        for control in window_random_controls(
            event, count=5, window=window, rng=rng
        )
    ]

    layout = temporal_feature_layout()
    event_matrix, _ = build_temporal_matrix(events)
    control_matrix, _ = build_temporal_matrix(confined)

    imbalance = feature_imbalance(event_matrix, control_matrix, layout)
    balance = era_balance(events, confined, window)

    assert balance["fraction_outside_event_window"] == 0.0
    # Far below the >1.0 the out-of-era design produced.
    assert imbalance["max_absolute_standardized_difference"] < 0.6
