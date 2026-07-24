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
TEMPORAL_SCHEMA_VERSION = "1.0.0"

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


def temporal_feature_layout() -> tuple[str, ...]:
    """Return the fixed column labels of a temporal state vector."""
    return tuple(
        f"{body}|{quantity}"
        for body in ORDERED_BODIES
        for quantity in ORDERED_QUANTITIES
    )


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

    def content_hash(self) -> str:
        """Return a hash over the semantic content only.

        Excludes nothing volatile, because a temporal state has no volatile
        provenance: it is a pure function of the instant and the schema.
        Two runs must therefore agree exactly.
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
        birth_time=f"{int(hour):02d}:{int((hour % 1) * 60):02d}",
        birth_place="",
        latitude=0.0,
        longitude=0.0,
        timezone="UTC",
        time_known=True,
    )

    result = build_ephemeris(birth)

    values: list[float] = []

    for body in ORDERED_BODIES:
        position = result.planets.get(body)

        if position is None:
            raise TemporalStateError(
                f"Ephemeris did not return a position for {body!r} at "
                f"{moment.isoformat()}."
            )

        radians = np.deg2rad(float(position.longitude))

        values.extend(
            (
                float(np.cos(radians)),
                float(np.sin(radians)),
                float(position.latitude),
                float(position.speed),
                1.0 if position.retrograde else 0.0,
            )
        )

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
