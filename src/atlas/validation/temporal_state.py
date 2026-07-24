"""Deterministic temporal state vectors for statistical testing.

The temporal branch begins where the identity branch ends, and shares none of
its inputs. A temporal state is a function of one thing: an explicit UTC
instant. No names, no birth data, no profile.

The first temporal milestone is not "does astrology work". It is whether
Atlas can produce temporal representations reproducible enough to test
anything at all. That means:

* an explicit evaluation instant, never "now" and never a placeholder epoch
* a pinned ephemeris engine, recorded with the result
* a hashed temporal feature schema, so a change in what a temporal feature
  *means* invalidates the artifacts built against it
* byte-identical output for repeated runs

Everything downstream -- event cohorts, matched date controls, Kamea
geometry -- rests on that, so it is established first and separately.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import json
from typing import Any, Iterable, Sequence

import numpy as np

from atlas.temporal.ephemeris import build_ephemeris
from atlas.temporal.models import BirthData


TEMPORAL_STATE_SCHEMA = "atlas.validation.temporal-state.v1"
# Bumped when the feature set changes. Pairwise angular separations were
# added in 1.1.0, which changes the layout and therefore the schema hash.
TEMPORAL_SCHEMA_VERSION = "1.1.0"

# The bodies a temporal state records, in fixed order. Order is part of the
# schema: reordering changes the vector layout and so must change its hash.
ORDERED_BODIES: tuple[str, ...] = (
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
)

# Per-body quantities. Longitude is angular, so it is encoded as a
# (cos, sin) pair: a raw degree value would place 359 deg and 1 deg at
# opposite ends of the range when they are two degrees apart.
ORDERED_QUANTITIES: tuple[str, ...] = (
    "longitude_cos",
    "longitude_sin",
    "latitude",
    "speed",
    "retrograde",
)


def ordered_body_pairs() -> tuple[tuple[str, str], ...]:
    """Return every unordered body pair, in fixed order."""
    return tuple(
        (ORDERED_BODIES[i], ORDERED_BODIES[j])
        for i in range(len(ORDERED_BODIES))
        for j in range(i + 1, len(ORDERED_BODIES))
    )


def temporal_feature_layout() -> tuple[str, ...]:
    """Return the fixed column labels of a temporal state vector.

    Per-body quantities first, then pairwise angular separations. The
    separations are part of the *raw* representation because relative
    geometry is available directly from the coordinates -- it is not an
    engineered feature, and omitting it would make the raw baseline
    artificially weak in any later comparison.
    """
    per_body = tuple(
        f"{body}|{quantity}"
        for body in ORDERED_BODIES
        for quantity in ORDERED_QUANTITIES
    )

    pairwise = tuple(
        f"{left}~{right}|separation_{component}"
        for left, right in ordered_body_pairs()
        for component in ("cos", "sin")
    )

    return per_body + pairwise


def temporal_schema_hash() -> str:
    """Return a deterministic hash of the temporal feature schema.

    Mirrors the identity layer's feature-schema hash and exists for the same
    reason: an artifact built against a different notion of "temporal
    feature" is stale even when its inputs are unchanged.
    """
    payload = {
        "schema": TEMPORAL_STATE_SCHEMA,
        "schema_version": TEMPORAL_SCHEMA_VERSION,
        "bodies": list(ORDERED_BODIES),
        "quantities": list(ORDERED_QUANTITIES),
        "pairs": [list(pair) for pair in ordered_body_pairs()],
        "layout": list(temporal_feature_layout()),
    }

    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


class TemporalStateError(ValueError):
    """A temporal state could not be built deterministically."""


@dataclass(frozen=True, slots=True)
class TemporalState:
    """Planetary state at one explicit instant."""

    instant: datetime
    julian_day: float
    ephemeris_engine_version: str
    schema_hash: str
    layout: tuple[str, ...]
    values: tuple[float, ...]

    def as_array(self) -> np.ndarray:
        """Return the state as a float array."""
        return np.asarray(self.values, dtype=np.float64)

    def values_hash(self) -> str:
        """Return a hash over the state *values* alone.

        Deliberately excludes the instant, so that two different times
        producing the same sky are detectable. ``content_hash`` cannot serve
        this purpose: it includes the instant, so every state is unique by
        construction and no collision could ever be found.
        """
        payload = {
            "schema_hash": self.schema_hash,
            "values": [round(float(v), 12) for v in self.values],
        }

        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()

    def content_hash(self) -> str:
        """Return a hash over the instant and its state.

        Used for reproducibility checks: the same instant must always
        produce the same state. For collision detection use
        :meth:`values_hash`, which omits the instant.
        """
        payload = {
            "instant": self.instant.isoformat(),
            "schema_hash": self.schema_hash,
            # Rounded to a precision far finer than any downstream use, so
            # the hash is stable against last-bit noise while remaining
            # sensitive to any real difference.
            "values": [round(float(v), 12) for v in self.values],
        }

        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema": TEMPORAL_STATE_SCHEMA,
            "instant": self.instant.isoformat(),
            "julian_day": self.julian_day,
            "ephemeris_engine_version": self.ephemeris_engine_version,
            "schema_hash": self.schema_hash,
            "content_hash": self.content_hash(),
            "values_hash": self.values_hash(),
            "layout": list(self.layout),
            "values": list(self.values),
        }


def require_utc(instant: datetime) -> datetime:
    """Return the instant, insisting it is timezone-aware UTC.

    A naive datetime is rejected rather than assumed: silently treating local
    time as UTC would shift every position by the machine's offset and make
    results depend on where they were computed.
    """
    if instant.tzinfo is None:
        raise TemporalStateError(
            "Temporal states require a timezone-aware UTC instant. A naive "
            "datetime would be interpreted differently on machines in "
            "different time zones."
        )

    return instant.astimezone(UTC)


def build_temporal_state(instant: datetime) -> TemporalState:
    """Build the planetary state at one explicit UTC instant."""
    moment = require_utc(instant)

    hour = (
        moment.hour
        + moment.minute / 60.0
        + moment.second / 3600.0
        + moment.microsecond / 3_600_000_000.0
    )

    # The ephemeris entry point is birth-shaped; a temporal state is simply
    # the same calculation with the "birth" being the evaluation instant.
    # Location is fixed at the geocentric origin because a temporal state
    # describes the sky, not an observer.
    birth = BirthData(
        name="temporal-state",
        birth_date=f"{moment.year:04d}-{moment.month:02d}-{moment.day:02d}",
        # HH:MM:SS, not HH:MM. The ephemeris accepts seconds, and
        # formatting without them silently quantized every instant to the
        # minute -- which would make sub-minute event timestamps
        # indistinguishable.
        birth_time=(
            f"{moment.hour:02d}:{moment.minute:02d}:{moment.second:02d}"
        ),
        birth_place="",
        latitude=0.0,
        longitude=0.0,
        timezone="UTC",
        time_known=True,
    )

    result = build_ephemeris(birth)

    values: list[float] = []
    longitudes: dict[str, float] = {}

    for body in ORDERED_BODIES:
        position = result.planets.get(body)

        if position is None:
            raise TemporalStateError(
                f"Ephemeris did not return a position for {body!r} at "
                f"{moment.isoformat()}."
            )

        radians = np.deg2rad(float(position.longitude))
        longitudes[body] = radians

        values.extend(
            (
                float(np.cos(radians)),
                float(np.sin(radians)),
                float(position.latitude),
                float(position.speed),
                1.0 if position.retrograde else 0.0,
            )
        )

    # Pairwise angular separation, again as (cos, sin) so the wrap at 360
    # degrees does not create a false discontinuity.
    for left, right in ordered_body_pairs():
        separation = longitudes[left] - longitudes[right]
        values.extend((float(np.cos(separation)), float(np.sin(separation))))

    return TemporalState(
        instant=moment,
        julian_day=float(result.julian_day),
        ephemeris_engine_version=str(result.version),
        schema_hash=temporal_schema_hash(),
        layout=temporal_feature_layout(),
        values=tuple(values),
    )


def build_temporal_matrix(
    instants: Sequence[datetime],
) -> tuple[np.ndarray, list[TemporalState]]:
    """Build a matrix of temporal states, one row per instant."""
    states = [build_temporal_state(instant) for instant in instants]

    if not states:
        return np.empty((0, len(temporal_feature_layout()))), []

    return np.vstack([state.as_array() for state in states]), states


def matched_date_controls(
    instant: datetime,
    *,
    count: int = 10,
    minimum_offset_days: int = 90,
    maximum_offset_days: int = 3650,
    seed: int = 0,
) -> list[datetime]:
    """Return control instants offset from a real event.

    Offsets start at a minimum distance so a control is not effectively the
    same sky as the event, and are drawn symmetrically before and after so
    the control set carries no net direction in time.
    """
    if minimum_offset_days >= maximum_offset_days:
        raise TemporalStateError(
            "minimum_offset_days must be less than maximum_offset_days."
        )

    moment = require_utc(instant)
    rng = np.random.default_rng(seed)

    controls: list[datetime] = []

    for index in range(count):
        magnitude = int(
            rng.integers(minimum_offset_days, maximum_offset_days + 1)
        )
        direction = 1 if index % 2 == 0 else -1

        controls.append(moment + timedelta(days=direction * magnitude))

    return controls


def verify_determinism(
    instants: Iterable[datetime],
    *,
    repeats: int = 3,
) -> dict[str, Any]:
    """Recompute states several times and report whether they agree.

    The milestone-1 acceptance check. Compares content hashes rather than
    floats so the answer is a clean yes or no.
    """
    moments = list(instants)
    per_instant: list[dict[str, Any]] = []
    all_stable = True

    for moment in moments:
        hashes = {
            build_temporal_state(moment).content_hash()
            for _ in range(repeats)
        }
        stable = len(hashes) == 1
        all_stable &= stable

        per_instant.append(
            {
                "instant": require_utc(moment).isoformat(),
                "repeats": repeats,
                "distinct_hashes": len(hashes),
                "stable": stable,
            }
        )

    return {
        "instants": len(moments),
        "repeats": repeats,
        "all_stable": all_stable,
        "unstable": [row for row in per_instant if not row["stable"]],
        "per_instant": per_instant,
    }


# Staged panel sizes. Regular cadence can alias against orbital periods, so
# every panel is paired with a seeded random sample that cannot.
PANEL_PRESETS: dict[str, dict[str, Any]] = {
    "smoke": {"years": 2, "cadence_hours": 24},
    "development": {"years": 50, "cadence_hours": 12},
    "full": {"years": 200, "cadence_hours": 12},
}


def build_temporal_panel(
    *,
    start: datetime,
    end: datetime,
    cadence_hours: int,
    random_samples: int = 0,
    seed: int = 0,
) -> list[datetime]:
    """Return a deterministic panel of instants, plus a random sample.

    The regular cadence is reproducible and easy to reason about; the random
    sample exists because a fixed cadence can land in phase with a periodic
    signal and make a representation look more or less stable than it is.
    """
    start_utc = require_utc(start)
    end_utc = require_utc(end)

    if start_utc >= end_utc:
        raise TemporalStateError("start must be earlier than end.")

    if cadence_hours <= 0:
        raise TemporalStateError("cadence_hours must be positive.")

    step = timedelta(hours=cadence_hours)
    instants: list[datetime] = []

    moment = start_utc

    while moment < end_utc:
        instants.append(moment)
        moment += step

    if random_samples > 0:
        rng = np.random.default_rng(seed)
        span_seconds = int((end_utc - start_utc).total_seconds())

        instants.extend(
            start_utc + timedelta(seconds=int(offset))
            for offset in rng.integers(0, span_seconds, random_samples)
        )

    return instants


def panel_from_preset(
    preset: str,
    *,
    end: datetime | None = None,
    random_samples: int = 500,
    seed: int = 0,
) -> list[datetime]:
    """Return a panel for a named preset, ending at a fixed instant."""
    if preset not in PANEL_PRESETS:
        raise TemporalStateError(
            f"Unknown panel preset {preset!r}. "
            f"Expected one of {sorted(PANEL_PRESETS)}."
        )

    settings = PANEL_PRESETS[preset]
    # A fixed default end date, never "now": the panel must not change
    # depending on when it is generated.
    finish = require_utc(end or datetime(2040, 1, 1, tzinfo=UTC))
    begin = finish - timedelta(days=365 * int(settings["years"]))

    return build_temporal_panel(
        start=begin,
        end=finish,
        cadence_hours=int(settings["cadence_hours"]),
        random_samples=random_samples,
        seed=seed,
    )
