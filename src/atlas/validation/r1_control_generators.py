"""Candidate control generators for R1, and the proof that one works.

The gate built in :mod:`r1_control_quality` can reject a masked cohort. It
cannot show that an acceptable cohort is constructible, and a refusal boundary
that nothing can pass is not a working framework. This module closes that gap.

The test is deliberately not "do the calendar-year histograms match". A
generator must remove **representation-level separability** -- Saturn's B3D
classes must stop distinguishing events from controls -- not merely match a
source variable presumed to cause it::

    inadequate controls   -> Saturn B3D separates events from controls
                          -> gate rejects

    era-matched controls  -> separability returns to null
                          -> support and saturation checks pass
                          -> gate accepts

The label is **event versus control**, not early versus late. Balance is the
question; era is the mechanism. Validation stays blocked by calendar year for
the same reason as everywhere else: a random split lets two instants sharing a
Saturn phase land on both sides and makes a poor generator look successful.

``representation_matched`` is included as a diagnostic upper bound, not as a
canonical choice. Matching directly on Saturn's B3D class answers "can the
leakage be removed at all", but it conditions away the very feature under
study -- so if simpler era matching achieves the same result, that is the one
to freeze.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Callable, Sequence

import numpy as np

from atlas.validation.kamea_baselines import encode_cohort
from atlas.validation.kamea_era import era_association
from atlas.validation.r1_control_quality import (
    MAX_ERA_ACCURACY,
    MIN_SUPPORT_OVERLAP,
    dominant_share,
    support_overlap,
    total_variation,
)
from atlas.validation.temporal_kamea import canonical_spec

GENERATOR_SCHEMA = "atlas.validation.r1-control-generators.v1"

OBSERVATION_START = datetime(1970, 1, 1, tzinfo=UTC)
OBSERVATION_END = datetime(2025, 12, 31, tzinfo=UTC)

# Several frozen contrasts with different gaps and positions, so the proof
# cannot rest on one fortunate pairing. The first is the permanent regression
# case used by the Saturn gate.
ERA_CONTRASTS: dict[str, tuple[datetime, datetime]] = {
    "late_2010s": (
        datetime(2010, 1, 1, tzinfo=UTC),
        datetime(2020, 1, 1, tzinfo=UTC),
    ),
    "early_1970s": (
        datetime(1970, 1, 1, tzinfo=UTC),
        datetime(1980, 1, 1, tzinfo=UTC),
    ),
    "mid_1990s": (
        datetime(1993, 1, 1, tzinfo=UTC),
        datetime(1999, 1, 1, tzinfo=UTC),
    ),
}


def draw_events(
    contrast: str, count: int, seed: int
) -> list[datetime]:
    """Draw an era-skewed event cohort inside one frozen contrast window."""
    start, end = ERA_CONTRASTS[contrast]
    rng = np.random.default_rng(seed)
    span = int((end - start).total_seconds())

    return sorted(
        start + timedelta(seconds=int(rng.integers(0, span)))
        for _ in range(count)
    )


# ---------------------------------------------------------------------------
# Candidate generators
# ---------------------------------------------------------------------------


def window_uniform_controls(
    events: Sequence[datetime], *, per_event: int, seed: int, **_: Any
) -> list[datetime]:
    """Draw uniformly across the observation window.

    The inadequate baseline. It ignores the event cohort's era entirely, so
    it is expected to fail -- and a proof that shows only successes has not
    demonstrated that the gate discriminates.
    """
    rng = np.random.default_rng(seed)
    span = int((OBSERVATION_END - OBSERVATION_START).total_seconds())

    return [
        OBSERVATION_START + timedelta(seconds=int(rng.integers(0, span)))
        for _ in range(len(events) * per_event)
    ]


def stratified_era_controls(
    events: Sequence[datetime],
    *,
    per_event: int,
    seed: int,
    block_years: int = 1,
    **_: Any,
) -> list[datetime]:
    """Draw within the same calendar block as each event.

    The direct causal response to the observed mechanism: Saturn's cell is
    approximately a decade label, so holding the block fixed holds the cell
    distribution fixed without conditioning on the representation itself.
    """
    rng = np.random.default_rng(seed)
    controls: list[datetime] = []

    for event in events:
        block_start = datetime(
            event.year - (event.year % block_years), 1, 1, tzinfo=UTC
        )
        block_end = datetime(
            block_start.year + block_years, 1, 1, tzinfo=UTC
        )
        span = int((block_end - block_start).total_seconds())

        controls.extend(
            block_start + timedelta(seconds=int(rng.integers(0, span)))
            for _ in range(per_event)
        )

    return controls


def symmetric_displacement_controls(
    events: Sequence[datetime],
    *,
    per_event: int,
    seed: int,
    displacement_days: int = 180,
    **_: Any,
) -> list[datetime]:
    """Place controls at t +/- delta, both directions represented.

    Worked well for R0, but needs its own proof at R1: Saturn's bins are
    coarse and long-lived, so a displacement small enough to stay inside the
    window may also be small enough to leave the cell unchanged.
    """
    rng = np.random.default_rng(seed)
    controls: list[datetime] = []

    for event in events:
        for index in range(per_event):
            magnitude = timedelta(
                days=float(rng.uniform(1, displacement_days))
            )
            sign = 1 if index % 2 == 0 else -1
            candidate = event + sign * magnitude

            if OBSERVATION_START <= candidate <= OBSERVATION_END:
                controls.append(candidate)
            else:
                controls.append(event - sign * magnitude)

    return controls


def representation_matched_controls(
    events: Sequence[datetime],
    *,
    per_event: int,
    seed: int,
    scale: str = "R1-W3D",
    **_: Any,
) -> list[datetime]:
    """Match directly on Saturn's B3D class.

    The strongest guarantee and a changed estimand: Saturn's B3D can no
    longer contribute to event/control discrimination, because it was
    conditioned on. Kept as a diagnostic upper bound answering "can the
    leakage be removed at all", never as the canonical generator.
    """
    rng = np.random.default_rng(seed)
    spec = canonical_spec(scale)

    # Build a pool spanning the window, indexed by its Saturn class.
    span = int((OBSERVATION_END - OBSERVATION_START).total_seconds())
    pool = sorted(
        OBSERVATION_START + timedelta(seconds=int(rng.integers(0, span)))
        for _ in range(len(events) * per_event * 4)
    )

    pool_classes = [
        item["B3D"] for item in encode_cohort(pool, "saturn", spec)
    ]
    by_class: dict[Any, list[datetime]] = {}

    for instant, signature in zip(pool, pool_classes):
        by_class.setdefault(signature, []).append(instant)

    event_classes = [
        item["B3D"] for item in encode_cohort(list(events), "saturn", spec)
    ]

    controls: list[datetime] = []

    for signature in event_classes:
        candidates = by_class.get(signature)

        if not candidates:
            continue

        controls.extend(
            candidates[int(rng.integers(0, len(candidates)))]
            for _ in range(per_event)
        )

    return controls


GENERATORS: dict[str, Callable[..., list[datetime]]] = {
    "window_uniform": window_uniform_controls,
    "stratified_era": stratified_era_controls,
    "symmetric_displacement": symmetric_displacement_controls,
    "representation_matched": representation_matched_controls,
}

# Expected to fail by construction. A proof in which every candidate passes
# has not shown the gate discriminates.
EXPECTED_INADEQUATE: tuple[str, ...] = ("window_uniform",)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GeneratorVerdict:
    """Whether one generator produced an acceptable cohort."""

    generator: str
    contrast: str
    scale: str
    seed: int
    diagnostics: dict[str, Any]

    @property
    def separable(self) -> bool:
        """Return whether Saturn's B3D distinguishes events from controls."""
        upstream = self.diagnostics["B3D"]

        return (
            upstream["balanced_accuracy"] >= MAX_ERA_ACCURACY
            and upstream["mi_p_value"] < 0.05
        )

    @property
    def acceptable(self) -> bool:
        """Return whether every upstream condition passes."""
        return (
            not self.separable
            and self.diagnostics["support_overlap"] >= MIN_SUPPORT_OVERLAP
            and not self.diagnostics["masking"]
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "generator": self.generator,
            "contrast": self.contrast,
            "scale": self.scale,
            "seed": self.seed,
            "separable": self.separable,
            "acceptable": self.acceptable,
            **self.diagnostics,
        }


def evaluate_generator(
    generator: str,
    contrast: str,
    *,
    scale: str = "R1-W3D",
    events: int = 60,
    per_event: int = 2,
    seed: int = 20260801,
    permutations: int = 100,
) -> GeneratorVerdict:
    """Test whether one generator removes Saturn's B3D separability."""
    event_instants = draw_events(contrast, events, seed)
    control_instants = GENERATORS[generator](
        event_instants, per_event=per_event, seed=seed + 1, scale=scale
    )

    instants = list(event_instants) + list(control_instants)
    labels = ["event"] * len(event_instants) + [
        "control"
    ] * len(control_instants)

    spec = canonical_spec(scale)
    encodings = encode_cohort(instants, "saturn", spec)

    diagnostics: dict[str, Any] = {}

    for name in ("B3", "B3D", "B2"):
        signatures = [item[name] for item in encodings]
        diagnostics[name] = era_association(
            signatures,
            instants,
            labels,
            permutations=permutations,
            seed=seed,
        )

    event_b3d = [
        item["B3D"] for item in encodings[: len(event_instants)]
    ]
    control_b3d = [
        item["B3D"] for item in encodings[len(event_instants) :]
    ]

    upstream_separable = (
        diagnostics["B3D"]["balanced_accuracy"] >= MAX_ERA_ACCURACY
        and diagnostics["B3D"]["mi_p_value"] < 0.05
    )
    downstream_clean = diagnostics["B2"]["balanced_accuracy"] < (
        MAX_ERA_ACCURACY
    )

    diagnostics.update(
        {
            "events": len(event_instants),
            "controls": len(control_instants),
            "support_overlap": support_overlap(event_b3d, control_b3d),
            "class_imbalance": total_variation(event_b3d, control_b3d),
            "dominant_share": dominant_share(event_b3d + control_b3d),
            # The structural rule, evaluated for this cohort.
            "masking": upstream_separable and downstream_clean,
        }
    )

    return GeneratorVerdict(
        generator=generator,
        contrast=contrast,
        scale=scale,
        seed=seed,
        diagnostics=diagnostics,
    )


def prove_generator(
    generator: str,
    *,
    contrasts: Sequence[str] = tuple(ERA_CONTRASTS),
    scales: Sequence[str] = ("R1-W3D", "R1-W1Y"),
    seeds: Sequence[int] = (20260801, 20260802),
    events: int = 60,
    per_event: int = 2,
    permutations: int = 100,
) -> dict[str, Any]:
    """Return whether a generator is acceptable across every condition.

    "Constructible" is operational: it must hold across multiple frozen era
    contrasts, multiple deterministic seeds and every canonical scale tested.
    One passing configuration is not a proof.
    """
    verdicts = [
        evaluate_generator(
            generator,
            contrast,
            scale=scale,
            events=events,
            per_event=per_event,
            seed=seed,
            permutations=permutations,
        )
        for contrast in contrasts
        for scale in scales
        for seed in seeds
    ]

    failures = [
        f"{v.contrast}/{v.scale}/{v.seed}" for v in verdicts if not v.acceptable
    ]

    return {
        "generator": generator,
        "conditions": len(verdicts),
        "acceptable_everywhere": not failures,
        "failing_conditions": failures,
        "expected_inadequate": generator in EXPECTED_INADEQUATE,
        "verdicts": [verdict.to_dict() for verdict in verdicts],
    }
