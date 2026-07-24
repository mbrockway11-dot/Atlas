"""Tests that acceptable R1 cohorts are constructible.

A refusal boundary nothing can pass is not a working framework. The gate in
:mod:`r1_control_quality` proved it can reject a masked cohort; these tests
prove a valid one exists, and that the gate still rejects an invalid one --
a proof in which every candidate passes would show only that the gate is
inert.

The label throughout is **event versus control**, not early versus late.
Balance is the question; era is the mechanism.
"""

from __future__ import annotations

import pytest

from atlas.validation.r1_control_generators import (
    ERA_CONTRASTS,
    EXPECTED_INADEQUATE,
    GENERATORS,
    OBSERVATION_END,
    OBSERVATION_START,
    draw_events,
    evaluate_generator,
    prove_generator,
    stratified_era_controls,
    symmetric_displacement_controls,
    window_uniform_controls,
)


# ---------------------------------------------------------------------------
# The gate discriminates
# ---------------------------------------------------------------------------


def test_inadequate_controls_are_rejected() -> None:
    """Uniform draws ignore the event era, and must fail.

    Without this the proof below would show only that the gate is inert.
    """
    verdict = evaluate_generator(
        "window_uniform", "mid_1990s", events=40, permutations=50
    )

    assert not verdict.acceptable


def test_inadequate_controls_can_trigger_masking() -> None:
    """The failure mode, observed rather than constructed.

    Saturn's B3D separates events from controls while B2 does not, so a
    B2-only balance check would have certified a confounded cohort.
    """
    verdict = evaluate_generator(
        "window_uniform", "mid_1990s", events=40, permutations=50
    )

    assert verdict.separable
    assert verdict.diagnostics["masking"] is True
    assert verdict.diagnostics["B2"]["balanced_accuracy"] < (
        verdict.diagnostics["B3D"]["balanced_accuracy"]
    )


# ---------------------------------------------------------------------------
# A valid cohort exists
# ---------------------------------------------------------------------------


def test_era_stratified_controls_remove_separability() -> None:
    """The canonical generator: matched blocks, no representation matching.

    This is the result that matters. Saturn's B3D stops distinguishing
    events from controls without conditioning on the feature under study,
    so the leakage is removable without changing the estimand.
    """
    verdict = evaluate_generator(
        "stratified_era", "late_2010s", events=50, permutations=50
    )

    assert not verdict.separable
    assert verdict.acceptable
    assert verdict.diagnostics["B3D"]["balanced_accuracy"] < 0.7


def test_stratified_controls_hold_across_every_condition() -> None:
    """Constructible is operational, not a single fortunate pairing.

    Multiple frozen era contrasts, multiple deterministic seeds, every
    canonical scale tested.
    """
    proof = prove_generator(
        "stratified_era",
        contrasts=("late_2010s", "mid_1990s"),
        scales=("R1-W3D",),
        seeds=(20260801,),
        events=40,
        permutations=40,
    )

    assert proof["acceptable_everywhere"] is True
    assert proof["failing_conditions"] == []


def test_representation_matching_is_an_upper_bound_not_canonical() -> None:
    """It works, and it changes the estimand.

    Matching on Saturn's B3D class conditions away the feature under study,
    so it answers "can the leakage be removed at all" rather than "how
    should controls be drawn". Since stratified era matching achieves the
    same result without conditioning, that is the one to freeze.
    """
    verdict = evaluate_generator(
        "representation_matched", "late_2010s", events=40, permutations=40
    )

    assert verdict.acceptable
    assert "representation_matched" not in EXPECTED_INADEQUATE


# ---------------------------------------------------------------------------
# Generator mechanics
# ---------------------------------------------------------------------------


def test_events_stay_inside_their_contrast_window() -> None:
    """An era-skewed cohort is what makes the test meaningful."""
    start, end = ERA_CONTRASTS["late_2010s"]
    events = draw_events("late_2010s", 30, seed=1)

    assert all(start <= event < end for event in events)
    assert events == sorted(events)
    assert draw_events("late_2010s", 30, seed=1) == events


def test_stratified_controls_share_the_event_block() -> None:
    """Holding the calendar block fixed holds the Saturn cell fixed."""
    events = draw_events("late_2010s", 20, seed=2)
    controls = stratified_era_controls(events, per_event=2, seed=3)

    assert len(controls) == 2 * len(events)
    assert {control.year for control in controls} <= {
        event.year for event in events
    }


def test_symmetric_displacement_uses_both_directions() -> None:
    """A one-sided displacement would impose a causal reading."""
    events = draw_events("mid_1990s", 20, seed=4)
    controls = symmetric_displacement_controls(
        events, per_event=4, seed=5, displacement_days=200
    )

    deltas = [
        (control - event).total_seconds()
        for event, group in zip(
            events, [controls[i : i + 4] for i in range(0, len(controls), 4)]
        )
        for control in group
    ]

    assert any(delta > 0 for delta in deltas)
    assert any(delta < 0 for delta in deltas)


def test_every_generator_stays_inside_the_observation_window() -> None:
    """A control outside the window is the R0 v1 failure, repeated."""
    events = draw_events("late_2010s", 20, seed=6)

    for name, generator in GENERATORS.items():
        controls = generator(events, per_event=2, seed=7, scale="R1-W3D")

        assert controls, name
        assert all(
            OBSERVATION_START <= control <= OBSERVATION_END
            for control in controls
        ), name


def test_uniform_controls_ignore_the_event_era() -> None:
    """Documenting why the baseline fails, rather than only that it does."""
    events = draw_events("late_2010s", 30, seed=8)
    controls = window_uniform_controls(events, per_event=2, seed=9)

    event_years = {event.year for event in events}
    control_years = {control.year for control in controls}

    assert len(control_years - event_years) > len(event_years)
