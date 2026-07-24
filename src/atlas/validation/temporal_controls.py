"""Control generators and era-balance diagnostics for temporal studies.

Temporal 2 v1 produced two significant results that were artifacts of its own
control design: the families that sampled outside the event window differed
from the events in slow-planet state for reasons unrelated to earthquakes.
Uranus, Neptune and Pluto have periods of 84, 165 and 248 years, so their
positions are close to an era label, and any generator that shifts the date
distribution also shifts the feature distribution.

Two things follow, and both live here.

First, era balance is no longer optional. Every control family reports where
its dates fall relative to the events, so a window mismatch is visible in the
result rather than diagnosed afterwards.

Second, the v2 generators are confined to the observation window by
construction. Candidates falling outside are **rejected and redrawn** rather
than reflected: reflection piles density at the boundaries, and rejection is
easier to state precisely.

Modulo wrapping is deliberately absent. Wrapping a 2025 event to 1970 would
invent a temporal relationship that does not exist.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Sequence

import numpy as np


CONTROL_SPEC_VERSION = "atlas.validation.temporal-controls.v2"

# How many redraws before a candidate is abandoned. Generous: with a
# 55-year window and offsets bounded well below it, rejection is rare.
MAX_REDRAWS = 200


class ControlGenerationError(ValueError):
    """A control family could not be generated within its window."""


@dataclass(frozen=True, slots=True)
class ObservationWindow:
    """The interval a control family must stay inside."""

    earliest: datetime
    latest: datetime

    def contains(self, moment: datetime) -> bool:
        """Return whether an instant lies within the window."""
        return self.earliest <= moment <= self.latest

    @property
    def span_seconds(self) -> int:
        """Return the window length in seconds."""
        return max(int((self.latest - self.earliest).total_seconds()), 1)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "earliest": self.earliest.isoformat(),
            "latest": self.latest.isoformat(),
            "span_days": self.span_seconds / 86_400.0,
        }


def window_from_events(events: Sequence[datetime]) -> ObservationWindow:
    """Return the observation window implied by an event set."""
    if not events:
        raise ControlGenerationError("Cannot infer a window from no events.")

    return ObservationWindow(earliest=min(events), latest=max(events))


def _draw_with_rejection(
    propose: Callable[[np.random.Generator], datetime],
    window: ObservationWindow,
    rng: np.random.Generator,
) -> datetime | None:
    """Propose candidates until one lands inside the window."""
    for _ in range(MAX_REDRAWS):
        candidate = propose(rng)

        if window.contains(candidate):
            return candidate

    return None


def matched_controls(
    event: datetime,
    *,
    count: int,
    window: ObservationWindow,
    rng: np.random.Generator,
    minimum_years: int = 1,
    maximum_years: int = 40,
) -> list[datetime]:
    """Whole-year offsets that stay inside the observation window.

    Holds season and Earth-Sun geometry roughly fixed while the slow planets
    move. v1's version drew the same offsets without a window check, which
    put 35.7% of controls outside 1970-2025 and produced its spurious result.
    """
    controls: list[datetime] = []

    for index in range(count):
        direction = 1 if index % 2 == 0 else -1

        def propose(generator: np.random.Generator) -> datetime:
            years = int(generator.integers(minimum_years, maximum_years + 1))
            # Sign alternates per draw but flips freely on redraw, so an
            # event near one edge can still find controls on the other side.
            sign = direction if generator.random() < 0.5 else -direction
            return event + timedelta(days=sign * years * 365)

        candidate = _draw_with_rejection(propose, window, rng)

        if candidate is not None:
            controls.append(candidate)

    return controls


def symmetric_shift_controls(
    event: datetime,
    *,
    count: int,
    window: ObservationWindow,
    rng: np.random.Generator,
    maximum_days: int = 5_000,
) -> list[datetime]:
    """Signed uniform shifts, rejected outside the window.

    v1 shifted forward only, which pushed 12.6% of controls past 2025 and
    gave the family a systematic era offset.
    """
    controls: list[datetime] = []

    for _ in range(count):

        def propose(generator: np.random.Generator) -> datetime:
            shift = int(generator.integers(-maximum_days, maximum_days + 1))
            return event + timedelta(days=shift)

        candidate = _draw_with_rejection(propose, window, rng)

        if candidate is not None:
            controls.append(candidate)

    return controls


def era_stratified_controls(
    event: datetime,
    *,
    count: int,
    window: ObservationWindow,
    rng: np.random.Generator,
    era_band_years: int = 2,
) -> list[datetime]:
    """Random instants drawn from the event's own era band.

    The strictest era control: slow-planet state is held nearly fixed by
    construction, so any remaining difference cannot be an era artifact.
    """
    controls: list[datetime] = []
    band_seconds = int(era_band_years * 365.25 * 86_400)

    for _ in range(count):

        def propose(generator: np.random.Generator) -> datetime:
            offset = int(generator.integers(-band_seconds, band_seconds + 1))
            return event + timedelta(seconds=offset)

        candidate = _draw_with_rejection(propose, window, rng)

        if candidate is not None:
            controls.append(candidate)

    return controls


def nearby_controls(
    event: datetime,
    *,
    count: int,
    window: ObservationWindow,
    rng: np.random.Generator,
    minimum_days: int = 3,
    maximum_days: int = 30,
) -> list[datetime]:
    """Days away from the event. Unchanged from v1.

    Already the cleanest family: at this scale the slow planets are
    essentially fixed, so it controls era almost automatically. It was null
    in v1 and its specification is deliberately carried over untouched.
    """
    controls: list[datetime] = []

    for index in range(count):
        direction = 1 if index % 2 == 0 else -1

        def propose(generator: np.random.Generator) -> datetime:
            offset = int(generator.integers(minimum_days, maximum_days + 1))
            sign = direction if generator.random() < 0.5 else -direction
            return event + timedelta(days=sign * offset)

        candidate = _draw_with_rejection(propose, window, rng)

        if candidate is not None:
            controls.append(candidate)

    return controls


def window_random_controls(
    event: datetime,
    *,
    count: int,
    window: ObservationWindow,
    rng: np.random.Generator,
) -> list[datetime]:
    """Uniform draws across the observation window. Unchanged from v1."""
    return [
        window.earliest
        + timedelta(seconds=int(rng.integers(0, window.span_seconds)))
        for _ in range(count)
    ]


CONTROL_FAMILIES: dict[str, Callable[..., list[datetime]]] = {
    "matched": matched_controls,
    "symmetric_shift": symmetric_shift_controls,
    "era_stratified": era_stratified_controls,
    "nearby": nearby_controls,
    "window_random": window_random_controls,
}


# ---------------------------------------------------------------------------
# Era balance
# ---------------------------------------------------------------------------


def era_balance(
    events: Sequence[datetime],
    controls: Sequence[datetime],
    window: ObservationWindow,
) -> dict[str, Any]:
    """Return how well a control family matches the events in time.

    Mandatory in every temporal result. v1 showed that a control family's
    date distribution *is* part of its feature distribution, so a study that
    does not report this cannot be interpreted.
    """
    if not controls:
        return {"controls": 0}

    event_years = np.array([moment.year for moment in events], dtype=float)
    control_years = np.array([moment.year for moment in controls], dtype=float)

    outside = sum(1 for moment in controls if not window.contains(moment))

    # Distribution distance over the shared year range, so a shift in mass
    # is visible even when the means happen to agree.
    low = int(min(event_years.min(), control_years.min()))
    high = int(max(event_years.max(), control_years.max()))
    bins = np.arange(low, high + 2)

    event_hist, _ = np.histogram(event_years, bins=bins, density=False)
    control_hist, _ = np.histogram(control_years, bins=bins, density=False)

    event_share = event_hist / max(event_hist.sum(), 1)
    control_share = control_hist / max(control_hist.sum(), 1)

    return {
        "controls": len(controls),
        "event_time_min": min(events).isoformat(),
        "event_time_max": max(events).isoformat(),
        "control_time_min": min(controls).isoformat(),
        "control_time_max": max(controls).isoformat(),
        "fraction_outside_event_window": outside / len(controls),
        # Total variation distance between the year distributions.
        "year_distribution_distance": float(
            0.5 * np.abs(event_share - control_share).sum()
        ),
        "mean_absolute_year_difference": float(
            abs(control_years.mean() - event_years.mean())
        ),
        "event_mean_year": float(event_years.mean()),
        "control_mean_year": float(control_years.mean()),
    }


def feature_imbalance(
    event_matrix: np.ndarray,
    control_matrix: np.ndarray,
    layout: Sequence[str],
    *,
    top: int = 15,
) -> dict[str, Any]:
    """Return per-feature standardized differences, largest first.

    Confirms the era mechanism directly rather than by orbital-period
    argument: if a control family is era-mismatched, the outer-planet
    components should dominate the imbalance.
    """
    if event_matrix.size == 0 or control_matrix.size == 0:
        return {"features": []}

    pooled = np.vstack((event_matrix, control_matrix))
    spread = pooled.std(axis=0)
    spread = np.where(spread == 0.0, 1.0, spread)

    differences = (
        event_matrix.mean(axis=0) - control_matrix.mean(axis=0)
    ) / spread

    order = np.argsort(np.abs(differences))[::-1][:top]

    ranked = [
        {
            "feature": str(layout[int(index)]),
            "standardized_difference": float(differences[int(index)]),
        }
        for index in order
    ]

    # Aggregate by body, so "which planets are imbalanced" is answerable
    # without reading the per-feature list.
    by_body: dict[str, list[float]] = {}

    for index, label in enumerate(layout):
        body = str(label).split("|")[0]
        by_body.setdefault(body, []).append(abs(float(differences[index])))

    body_means = {
        body: float(np.mean(values)) for body, values in by_body.items()
    }

    # An ordered LIST, not a dict. JSON serialization with sort_keys=True
    # re-alphabetizes keys, which silently destroyed this ranking once and
    # made a downstream check measure alphabetical position instead of
    # imbalance.
    body_ranking = [
        {"body": body, "mean_absolute_standardized_difference": value}
        for body, value in sorted(body_means.items(), key=lambda i: -i[1])
    ]

    return {
        "features": ranked,
        "max_absolute_standardized_difference": float(
            np.abs(differences).max()
        ),
        "mean_absolute_standardized_difference": float(
            np.abs(differences).mean()
        ),
        "body_ranking": body_ranking,
        "by_body_mean_absolute": body_means,
    }
