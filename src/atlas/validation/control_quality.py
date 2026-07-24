"""Required control-quality artifact for temporal studies.

Temporal 2 v1 produced a significant result that was an artifact of its own
control design. Nothing in the harness caught it: the diagnostics that
explained it were written afterwards, once the result looked wrong. That is
one investigation away from having been published as a finding.

So control quality is no longer something a study may add. It is a required
artifact, and the enforcement is structural: :func:`write_temporal_result`
refuses to write a result that does not carry one. A future study cannot
accidentally omit it, because omitting it means producing no output at all.

The artifact answers, for every control family:

    does it sample the same window as the events
    does it sample the same era distribution
    which features are most imbalanced, and by how much
    does the synthetic negative control still detect era leakage
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from atlas.validation.artifacts import write_json
from atlas.validation.temporal_controls import (
    ObservationWindow,
    era_balance,
    feature_imbalance,
    window_random_controls,
)


CONTROL_QUALITY_SCHEMA = "atlas.validation.control-quality.v1"

# Thresholds a control family must meet to be considered sound. Derived from
# the v1 failure: its two spurious families sampled 35.7% and 12.6% outside
# the window with imbalances of 0.611 and 0.419, while the two sound ones
# sampled 0.3% and 0.0% with imbalances near 0.09.
MAX_FRACTION_OUTSIDE_WINDOW = 0.01
MAX_FEATURE_IMBALANCE = 0.30
MAX_YEAR_DISTRIBUTION_DISTANCE = 0.35

# The imbalance threshold assumes a study of realistic size. A standardized
# difference between small samples carries sampling noise on its own, so a
# handful of events can exceed 0.30 with perfectly sound controls. Studies
# below this are reported but their soundness verdict is not meaningful.
MINIMUM_EVENTS_FOR_IMBALANCE_VERDICT = 100


class ControlQualityError(ValueError):
    """A temporal result was produced without control-quality evidence."""


@dataclass(frozen=True, slots=True)
class FamilyQuality:
    """Control-quality evidence for one family."""

    family: str
    era_balance: dict[str, Any]
    feature_imbalance: dict[str, Any]

    @property
    def fraction_outside_window(self) -> float:
        """Return the share of controls outside the event window."""
        return float(
            self.era_balance.get("fraction_outside_event_window", 1.0)
        )

    @property
    def max_imbalance(self) -> float:
        """Return the largest standardized feature difference."""
        return float(
            self.feature_imbalance.get(
                "max_absolute_standardized_difference", 1.0
            )
        )

    @property
    def year_distribution_distance(self) -> float:
        """Return the total-variation distance between year distributions."""
        return float(self.era_balance.get("year_distribution_distance", 1.0))

    def failures(self) -> list[str]:
        """Return the quality thresholds this family violates."""
        problems: list[str] = []

        if self.fraction_outside_window > MAX_FRACTION_OUTSIDE_WINDOW:
            problems.append("samples_outside_event_window")

        if self.max_imbalance > MAX_FEATURE_IMBALANCE:
            problems.append("excessive_feature_imbalance")

        if self.year_distribution_distance > MAX_YEAR_DISTRIBUTION_DISTANCE:
            problems.append("year_distribution_mismatch")

        return problems

    @property
    def sound(self) -> bool:
        """Return whether this family meets every quality threshold."""
        return not self.failures()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "family": self.family,
            "sound": self.sound,
            "failures": self.failures(),
            "temporal_window_overlap": 1.0 - self.fraction_outside_window,
            "fraction_outside_event_window": self.fraction_outside_window,
            "max_feature_imbalance": self.max_imbalance,
            "year_distribution_distance": self.year_distribution_distance,
            "era_balance": self.era_balance,
            "top_imbalanced_features": self.feature_imbalance.get(
                "features", []
            )[:10],
            "body_ranking": self.feature_imbalance.get("body_ranking", []),
        }


@dataclass(frozen=True, slots=True)
class ControlQuality:
    """The required control-quality artifact for one study."""

    schema_version: str
    families: tuple[FamilyQuality, ...]
    synthetic_control_check: dict[str, Any]

    @property
    def sound_families(self) -> tuple[str, ...]:
        """Return the families that meet every threshold."""
        return tuple(f.family for f in self.families if f.sound)

    @property
    def unsound_families(self) -> tuple[str, ...]:
        """Return the families that do not."""
        return tuple(f.family for f in self.families if not f.sound)

    @property
    def all_sound(self) -> bool:
        """Return whether every family is sound."""
        return not self.unsound_families

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema_version": self.schema_version,
            "all_families_sound": self.all_sound,
            "sound_families": list(self.sound_families),
            "unsound_families": list(self.unsound_families),
            "thresholds": {
                "max_fraction_outside_window": MAX_FRACTION_OUTSIDE_WINDOW,
                "max_feature_imbalance": MAX_FEATURE_IMBALANCE,
                "max_year_distribution_distance": (
                    MAX_YEAR_DISTRIBUTION_DISTANCE
                ),
            },
            "synthetic_control_check": self.synthetic_control_check,
            "families": [family.to_dict() for family in self.families],
            "interpretation": (
                "A family flagged unsound differs from the events in ways "
                "unrelated to the hypothesis. Any result from it measures "
                "the control design, not the events -- which is exactly "
                "what Temporal 2 v1 demonstrated."
            ),
        }


def synthetic_era_leak_check(
    *,
    build_matrix,
    layout: Sequence[str],
    seed: int = 20260801,
    sample: int = 30,
) -> dict[str, Any]:
    """Verify the harness can still detect era leakage.

    Runs the negative control inline: synthetic events from one decade
    against controls from another, where the labels carry no meaning. If the
    imbalance diagnostic no longer fires here, it is not capable of catching
    a real era confound either, and its silence on the study's own families
    means nothing.
    """
    from datetime import UTC

    rng = np.random.default_rng(seed)
    decade = int(timedelta(days=3652).total_seconds())

    events = [
        datetime(1970, 1, 1, tzinfo=UTC)
        + timedelta(seconds=int(rng.integers(0, decade)))
        for _ in range(sample)
    ]
    leaking = [
        datetime(2010, 1, 1, tzinfo=UTC)
        + timedelta(seconds=int(rng.integers(0, decade)))
        for _ in range(sample * 5)
    ]

    window = ObservationWindow(
        earliest=datetime(1970, 1, 1, tzinfo=UTC),
        latest=datetime(1980, 1, 1, tzinfo=UTC),
    )
    confined = [
        control
        for event in events
        for control in window_random_controls(
            event, count=5, window=window, rng=rng
        )
    ]

    event_matrix, _ = build_matrix(events)
    leaking_matrix, _ = build_matrix(leaking)
    confined_matrix, _ = build_matrix(confined)

    leaking_imbalance = feature_imbalance(
        event_matrix, leaking_matrix, layout
    )["max_absolute_standardized_difference"]
    confined_imbalance = feature_imbalance(
        event_matrix, confined_matrix, layout
    )["max_absolute_standardized_difference"]

    # Confinement is judged by how much of the leak it removes, not by an
    # absolute ceiling. A standardized difference carries sampling noise
    # that grows as the sample shrinks, so a fixed bound would fail on small
    # runs for reasons having nothing to do with the diagnostic.
    removed = confined_imbalance < 0.5 * leaking_imbalance
    detected = leaking_imbalance > 1.0 and removed

    return {
        "out_of_era_max_imbalance": float(leaking_imbalance),
        "window_confined_max_imbalance": float(confined_imbalance),
        "leak_reduction_ratio": (
            float(confined_imbalance / leaking_imbalance)
            if leaking_imbalance > 0
            else 1.0
        ),
        "leak_detected": bool(leaking_imbalance > 1.0),
        "confinement_removes_leak": bool(removed),
        "diagnostic_working": bool(detected),
        "note": (
            "Synthetic labels carry no meaning. Any separation in the "
            "out-of-era arm is era leakage alone. If diagnostic_working is "
            "false, this study's control-quality evidence is unreliable."
        ),
    }


def build_control_quality(
    *,
    events: Sequence[datetime],
    controls_by_family: dict[str, Sequence[datetime]],
    event_matrix: np.ndarray,
    control_matrices: dict[str, np.ndarray],
    layout: Sequence[str],
    window: ObservationWindow,
    build_matrix,
    seed: int = 20260801,
) -> ControlQuality:
    """Assemble the required control-quality artifact."""
    families = tuple(
        FamilyQuality(
            family=family,
            era_balance=era_balance(events, controls, window),
            feature_imbalance=feature_imbalance(
                event_matrix, control_matrices[family], layout
            ),
        )
        for family, controls in sorted(controls_by_family.items())
    )

    return ControlQuality(
        schema_version=CONTROL_QUALITY_SCHEMA,
        families=families,
        synthetic_control_check=synthetic_era_leak_check(
            build_matrix=build_matrix, layout=layout, seed=seed
        ),
    )


def write_temporal_result(
    result: dict[str, Any],
    *,
    control_quality: ControlQuality | None,
    output_dir: Path,
    result_name: str,
) -> dict[str, Path]:
    """Write a temporal result, refusing to do so without control quality.

    The enforcement point. A study that omits control-quality evidence
    produces no output rather than an unqualified number, because v1 showed
    that an unqualified number is indistinguishable from a finding.
    """
    if control_quality is None:
        raise ControlQualityError(
            "A temporal result cannot be written without control-quality "
            "evidence. Temporal 2 v1 produced a significant result that was "
            "an artifact of its control design, and nothing in the harness "
            "caught it. Build one with build_control_quality()."
        )

    if not control_quality.families:
        raise ControlQualityError(
            "Control quality carries no families; there is nothing to "
            "qualify the result with."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    quality_payload = control_quality.to_dict()

    # The result carries the verdict on its own controls, so a reader sees
    # it without opening a second file.
    annotated = {
        **result,
        "control_quality_summary": {
            "all_families_sound": control_quality.all_sound,
            "sound_families": list(control_quality.sound_families),
            "unsound_families": list(control_quality.unsound_families),
            "diagnostic_working": quality_payload[
                "synthetic_control_check"
            ]["diagnostic_working"],
        },
    }

    return {
        "result": write_json(annotated, output_dir / result_name),
        "control_quality": write_json(
            quality_payload, output_dir / "control_quality.json"
        ),
    }
