"""Temporal Kamea trajectories: R1 for the classical seven.

Temporal 1C asked how a planetary state becomes a Kamea state, and the first
answer attempted was the wrong shape. Measurement killed it: no Kamea
preserves locality (`tests/test_kamea_locality.py`), so pointwise continuity
is unobtainable, and planetary positions at a single instant are simultaneous
so they supply no ordering for a path processor that requires one.

The resolution is to stop treating an instant as a set of bodies and start
treating it as a set of *trajectories*. For classical body ``b`` at instant
``t``::

    S_b(t) = [q_b(lambda_b(t - m*delta_b)), ..., q_b(lambda_b(t)), ...,
              q_b(lambda_b(t + m*delta_b))]

Time supplies the ordering, so no convention has to be invented. Each body is
projected only onto its own traditional square, so planet-locality holds by
construction -- Mars never needs ordering relative to Venus.

Two invariants changed, and both changes are deliberate:

* **Pointwise continuity is dropped.** It is unsatisfiable, and pretending
  otherwise would mean declaring 360 boundaries per body and calling it a
  specification.
* **Path stability replaces it.** Nearby evaluation instants should produce
  similar paths, reduced paths and core geometries. That is falsifiable, and
  it is measured at four levels because reduction may absorb cell-level
  discontinuity or may merely hide it -- which of those it does is exactly
  what 1D has to find out.

Retrograde motion is deliberately *not* flagged. A chronological trajectory
already expresses reversal, stationarity, repeated cells and retracing; a
separate feature would duplicate that unless the audit shows the geometry
loses it.

**The frozen 1C result.** Measurement showed that a temporally local,
traditional, planet-native Kamea path cannot simultaneously give slow bodies
high discrimination: Saturn needs 3.27 years to cross one cell of its own
square, because the tradition pairs the slowest body with the coarsest one.
Rescuing both would mean abandoning "local", "traditional" or "planet-native".

So R1 does not claim to encode every body equally well at every scale. It
claims to represent *how much locally observable Kamea-cell traversal each
classical body exhibits around an instant at a fixed temporal resolution* --
at which the Moon is highly dynamic, Mercury and Venus usually move, and
Saturn and Jupiter are often static. The unevenness is part of the
representation, and :meth:`TemporalKameaPath.diagnostics` reports it rather
than hiding it.

R1 discards within-cell phase by construction; R0 preserves it. So the
question 2B must ask is not whether R1 beats R0, but whether R1 adds structure
*after conditioning on* R0.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Sequence

import numpy as np
import swisseph as swe

from atlas.kamea.path import KameaPath
from atlas.kamea.path_views import build_kamea_path_views
from atlas.kamea.squares import KAMEAS
from atlas.temporal.ephemeris import (
    calculate_planets,
    configure_ephemeris_path,
    DEFAULT_EPHEMERIS_PATH,
)
from atlas.validation.temporal_state import require_utc, temporal_schema_hash


TRAJECTORY_SCHEMA = "atlas.validation.temporal-kamea.v1"
TRAJECTORY_SPEC_VERSION = "1.0.0"

# The semantics of reduction and core-geometry extraction: reduce_value,
# project_values, and the render-path dedup that produces core geometry.
# Bump this when what those *mean* changes, not when they are refactored --
# a geometry built under different reduction semantics is a different object
# even from byte-identical inputs.
REDUCTION_VERSION = "1.0.0"

# The seven bodies with a traditional square. Uranus, Neptune and Pluto have
# neither a Kamea nor planetary-transform weights, so R1 covers seven of the
# ten bodies R0 records. Stated here rather than discovered downstream: an
# omission that is not written down is indistinguishable from a bug.
CLASSICAL_BODIES: dict[str, str] = {
    "saturn": "Saturn",
    "jupiter": "Jupiter",
    "mars": "Mars",
    "sun": "Sun",
    "venus": "Venus",
    "mercury": "Mercury",
    "moon": "Moon",
}

UNSUPPORTED_BODIES: tuple[str, ...] = ("Uranus", "Neptune", "Pluto")

# Mean daily motion in degrees, geocentric and apparent. Used only to size
# body-relative sampling steps, never as a feature -- so approximate values
# are appropriate and their imprecision cannot leak into a result.
MEAN_DAILY_MOTION: dict[str, float] = {
    "moon": 13.1764,
    "mercury": 4.0923,
    "sun": 0.9856,
    "venus": 1.6021,
    "mars": 0.5240,
    "jupiter": 0.0831,
    "saturn": 0.0335,
}


class SamplingFamily(str, Enum):
    """The trajectory-sampling families.

    Only ``FIXED_TIME`` is canonical. The other two are retained as
    characterization contrasts because they answer real questions, but they
    change what the object *means* and so cannot be the primary event
    representation -- see :data:`CANONICAL_FAMILY`.
    """

    # A single cadence for every body. Preserves real temporal motion, so the
    # Moon traverses far and Saturn barely moves -- which may be the physics
    # or may make square size and orbital speed inseparable.
    FIXED_TIME = "fixed_time"

    # Cadence scaled to each body's characteristic motion, so every body
    # traverses a comparable angular arc. Normalizes traversal at the cost of
    # spanning wildly different real durations.
    BODY_RELATIVE = "body_relative"

    # Added after both preregistered families failed the degeneracy
    # criterion, and added on the diagnosis rather than on any outcome: a
    # path cannot move unless its angular step is comparable to its own
    # quantization bin, and the bins differ by an order of magnitude across
    # the squares (40 degrees for Saturn, 4.44 for the Moon). This scales the
    # step to each body's *bin* rather than to a fixed arc.
    BIN_RELATIVE = "bin_relative"


# The canonical family. Every body shares one window, so the seven paths are
# observations of the same temporal neighbourhood.
#
# The alternatives buy cell occupancy by giving each body its own window,
# which means a Moon path describing two days sits alongside a Saturn path
# describing twenty years. Those geometries are still computable and still
# interesting -- they are R1b, a characterization contrast -- but they are not
# contemporaneous, so they cannot be the canonical representation of an
# instant.
CANONICAL_FAMILY = SamplingFamily.FIXED_TIME

# The canonical temporal scales. Each is a separately hashed representation
# with a single interpretable window, rather than one adaptive representation
# whose window varies per body. None may be selected by how it performs on
# events; 1D characterizes how discrimination and era dependence change with
# scale.
CANONICAL_SCALES: dict[str, timedelta] = {
    "R1-W3D": timedelta(days=3),
    "R1-W30D": timedelta(days=30),
    "R1-W180D": timedelta(days=180),
    "R1-W1Y": timedelta(days=365),
}

CANONICAL_HALF_WIDTH = 12


class TrajectoryError(ValueError):
    """A temporal Kamea trajectory could not be built as specified."""


@dataclass(frozen=True, slots=True)
class TrajectorySpec:
    """The frozen parameters of a trajectory representation.

    Every remaining design freedom in 1C lives here, so a result can always
    name the representation that produced it.
    """

    family: SamplingFamily
    # Half-width in samples: a path holds 2*half_width + 1 points.
    half_width: int = 6
    # FIXED_TIME: real time between samples.
    step: timedelta = timedelta(hours=6)
    # BODY_RELATIVE: degrees of that body's own mean motion per sample.
    angular_step_degrees: float = 1.0
    # BIN_RELATIVE: fraction of that body's own quantization bin per sample.
    bin_fraction: float = 0.5
    # Names the canonical scale this spec realizes, empty for ad-hoc specs.
    scale: str = ""
    # The window is centered. A trailing window would impose a causal
    # reading that suits neither births nor historical events; if a study
    # ever asks a predictive question it must define its own past-only
    # representation rather than quietly reusing this one.
    centered: bool = True
    # The identity pipeline expands values through a planet-specific
    # transform so large squares are not handed a low-range path. The
    # quantizer here already spans each square's full range, so the
    # transform would only add a fixed scramble. Off by default, recorded
    # either way.
    use_planetary_transform: bool = False

    def sample_offsets(self) -> tuple[int, ...]:
        """Return the sample indices, chronologically ordered."""
        if self.half_width < 1:
            raise TrajectoryError(
                "A trajectory needs at least one sample either side of the "
                "instant; a single point is a cell, not a path."
            )

        if self.centered:
            return tuple(range(-self.half_width, self.half_width + 1))

        return tuple(range(-2 * self.half_width, 1))

    def step_for(self, kamea_key: str) -> timedelta:
        """Return the sampling cadence for one body."""
        if self.family is SamplingFamily.FIXED_TIME:
            return self.step

        motion = MEAN_DAILY_MOTION[kamea_key]

        if self.family is SamplingFamily.BIN_RELATIVE:
            arc = quantization_bin_degrees(kamea_key) * self.bin_fraction
        else:
            arc = self.angular_step_degrees

        return timedelta(days=arc / motion)

    @property
    def canonical(self) -> bool:
        """Return whether this spec is a canonical R1 representation.

        Canonical means one shared window for all seven bodies, so the paths
        are contemporaneous. The body-relative families are diagnostic
        contrasts, not candidates.
        """
        return (
            self.family is CANONICAL_FAMILY
            and self.scale in CANONICAL_SCALES
            and self.centered
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "family": self.family.value,
            "scale": self.scale,
            "canonical": self.canonical,
            "half_width": self.half_width,
            "samples_per_path": len(self.sample_offsets()),
            "step_seconds": self.step.total_seconds(),
            "angular_step_degrees": self.angular_step_degrees,
            "bin_fraction": self.bin_fraction,
            "centered": self.centered,
            "use_planetary_transform": self.use_planetary_transform,
            "step_seconds_by_body": {
                key: self.step_for(key).total_seconds()
                for key in sorted(CLASSICAL_BODIES)
            },
        }

    def spec_hash(self) -> str:
        """Return a deterministic hash of the representation.

        Participates in artifact identity for the same reason the identity
        layer's feature-schema hash does: a path built under different
        parameters is a different object, not a stale one.
        """
        payload = {
            "schema": TRAJECTORY_SCHEMA,
            "spec_version": TRAJECTORY_SPEC_VERSION,
            "bodies": sorted(CLASSICAL_BODIES),
            **self.to_dict(),
        }

        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()


def representation_schema_hash(spec: TrajectorySpec) -> str:
    """Return the identity of a complete temporal representation.

    Closes the integrity gap where an artifact knew its ``spec_hash`` but the
    schema did not, so a change in the representation would not invalidate
    comparisons made across it. Composed of every input that changes what an
    R1 feature *means*::

        R0 feature schema  +  trajectory specification  +  canonical scale
                           +  reduction version

    Deliberately layered *on top of* :func:`temporal_schema_hash` rather than
    folded into it. The R0 hash is stamped into every raw-state artifact,
    including the frozen Temporal 2 v1 result; making it depend on the
    trajectory spec would change the recorded schema of frozen R0 studies
    whenever an R1 parameter moved, invalidating them for a reason that has
    nothing to do with them. R0 studies keep the R0 hash; R1 and R2 studies
    carry this one, which contains it.
    """
    payload = {
        "schema": TRAJECTORY_SCHEMA,
        "spec_version": TRAJECTORY_SPEC_VERSION,
        "reduction_version": REDUCTION_VERSION,
        "temporal_feature_schema_hash": temporal_schema_hash(),
        "trajectory_spec_hash": spec.spec_hash(),
        "scale": spec.scale,
        "bodies": sorted(CLASSICAL_BODIES),
        "square_sizes": {
            key: KAMEAS[key].size for key in sorted(CLASSICAL_BODIES)
        },
    }

    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def canonical_spec(
    scale: str = "R1-W3D", half_width: int = CANONICAL_HALF_WIDTH
) -> TrajectorySpec:
    """Return the canonical R1 spec at one temporal scale.

    Fixed window, shared by every body, centered on the instant. Slow bodies
    may produce stationary paths at any given scale; that is a property of
    the representation's temporal resolution, reported by
    :meth:`TemporalKameaPath.diagnostics`, not a defect to tune away.
    """
    window = CANONICAL_SCALES.get(scale)

    if window is None:
        raise TrajectoryError(
            f"{scale!r} is not a canonical scale. Choose one of "
            f"{', '.join(sorted(CANONICAL_SCALES))}, or build an explicit "
            "TrajectorySpec for a diagnostic contrast."
        )

    return TrajectorySpec(
        family=CANONICAL_FAMILY,
        half_width=half_width,
        step=window / half_width,
        scale=scale,
    )


@dataclass(frozen=True, slots=True)
class TemporalKameaPath:
    """One body's chronological trajectory projected onto its own square."""

    kamea_key: str
    body: str
    spec: TrajectorySpec
    instants: tuple[datetime, ...]
    longitudes: tuple[float, ...]
    values: tuple[int, ...]
    path: KameaPath

    @property
    def coordinates(self) -> tuple[tuple[int, int], ...]:
        """Return the projected path coordinates."""
        return self.path.coordinates

    @property
    def core_geometry(self) -> tuple[tuple[int, int], ...]:
        """Return the deduplicated shape, in first-visit order.

        The render path of the existing view machinery: repeated cells
        collapse, so this is the trajectory's shape rather than its dwell.
        """
        views = build_kamea_path_views(self.path)

        return tuple(
            (int(row), int(column))
            for row, column in views["render_path"]["coordinates"]
        )

    @property
    def occupancy(self) -> dict[int, int]:
        """Return how many samples landed on each reduced value."""
        counts: dict[int, int] = {}

        for value in self.path.reduced_values:
            counts[value] = counts.get(value, 0) + 1

        return counts

    @property
    def angular_span_degrees(self) -> float:
        """Return the arc traversed, unwrapped across the 360 boundary."""
        total = 0.0

        for earlier, later in zip(self.longitudes, self.longitudes[1:]):
            step = (later - earlier + 180.0) % 360.0 - 180.0
            total += abs(step)

        return total

    @property
    def reversals(self) -> int:
        """Return the number of direction changes in the trajectory.

        Retrograde behaviour, read off the path rather than flagged
        separately. If the geometry preserves this, no retrograde feature is
        needed; 1D decides whether it does.
        """
        steps = [
            (later - earlier + 180.0) % 360.0 - 180.0
            for earlier, later in zip(self.longitudes, self.longitudes[1:])
        ]
        signs = [1 if step > 0 else -1 for step in steps if step != 0]

        return sum(
            1 for a, b in zip(signs, signs[1:]) if a != b
        )

    @property
    def transition_count(self) -> int:
        """Return how many samples moved to a different cell."""
        return sum(
            1
            for a, b in zip(self.coordinates, self.coordinates[1:])
            if a != b
        )

    @property
    def longest_stationary_run(self) -> int:
        """Return the longest run of consecutive samples in one cell."""
        longest = current = 1

        for a, b in zip(self.coordinates, self.coordinates[1:]):
            current = current + 1 if a == b else 1
            longest = max(longest, current)

        return longest

    @property
    def path_distance(self) -> int:
        """Return the total Manhattan distance travelled on the grid."""
        return sum(
            abs(a[0] - b[0]) + abs(a[1] - b[1])
            for a, b in zip(self.coordinates, self.coordinates[1:])
        )

    @property
    def stationary(self) -> bool:
        """Return whether the path never left its starting cell.

        Reported rather than suppressed. A one-cell Saturn path is an honest
        statement about Saturn's motion at this temporal resolution, and
        dropping or expanding it would hide the representation's actual
        behaviour.
        """
        return len(set(self.coordinates)) == 1

    @property
    def core_shape(self) -> tuple[tuple[int, int], ...]:
        """Return the core geometry translated to its own origin.

        Translation-invariant, so two instants tracing the same figure in
        different regions of the square share a shape even though they share
        no cell.
        """
        geometry = self.core_geometry

        if not geometry:
            return ()

        row, column = geometry[0]

        return tuple((r - row, c - column) for r, c in geometry)

    def diagnostics(self) -> dict[str, Any]:
        """Return the reportable properties of this path.

        The canonical representation tolerates degeneracy, so degeneracy has
        to be visible. These are the fields an R1 study reports per body so
        that a stationary path reads as stationary rather than as missing.
        """
        square = KAMEAS[self.kamea_key]
        distinct = len(set(self.coordinates))

        return {
            "distinct_cells": distinct,
            "transition_count": self.transition_count,
            "occupancy_fraction": distinct / square.max_value,
            "longest_stationary_run": self.longest_stationary_run,
            "reversal_count": self.reversals,
            "path_distance": self.path_distance,
            "reduced_path_length": len(self.core_geometry),
            "core_shape": [list(cell) for cell in self.core_shape],
            "stationary": self.stationary,
            "angular_span_degrees": round(self.angular_span_degrees, 6),
        }

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "kamea_key": self.kamea_key,
            "body": self.body,
            "square_size": KAMEAS[self.kamea_key].size,
            "spec": self.spec.to_dict(),
            "representation_schema_hash": representation_schema_hash(
                self.spec
            ),
            "instants": [moment.isoformat() for moment in self.instants],
            "longitudes": [round(value, 9) for value in self.longitudes],
            "values": list(self.values),
            "reduced_values": list(self.path.reduced_values),
            "coordinates": [list(c) for c in self.coordinates],
            "core_geometry": [list(c) for c in self.core_geometry],
            "diagnostics": self.diagnostics(),
        }


def quantize_longitude(longitude: float, kamea_key: str) -> int:
    """Map a longitude into its body's square as an integer in [1, n^2].

    Uniform binning over the full circle, so every cell of the square is
    reachable and the inverse is bounded by half a bin. The bin width is
    360/n^2 degrees, which is 40 degrees for Saturn and 4.44 for the Moon --
    per-body resolution differs by design, following the tradition's own
    square sizes rather than imposing a uniform one.
    """
    square = KAMEAS[kamea_key]
    bins = square.max_value

    normalized = longitude % 360.0
    index = int(normalized / 360.0 * bins)

    # Guards the boundary: a longitude of exactly 360.0 minus an epsilon can
    # round to `bins` in floating point, which is one past the last cell.
    return min(index, bins - 1) + 1


def quantization_bin_degrees(kamea_key: str) -> float:
    """Return the angular width of one cell for this body."""
    return 360.0 / KAMEAS[kamea_key].max_value


def window_to_traverse(kamea_key: str, cells: float = 1.0) -> timedelta:
    """Return how long a body needs to cross ``cells`` of its own square.

    The locality-versus-window tension, made numeric. A trajectory only has
    geometry if it leaves its starting cell, and a body crosses a cell only
    as fast as its own motion allows against its own bin width. Saturn's bin
    is 40 degrees and Saturn moves 0.0335 degrees a day, so one cell costs
    roughly three years -- meaning no window short enough to describe an
    instant can give Saturn a non-degenerate path.

    This is structural, not a tuning failure: it follows from the tradition's
    own pairing of the slowest body with the smallest square.
    """
    arc = quantization_bin_degrees(kamea_key) * cells

    return timedelta(days=arc / MEAN_DAILY_MOTION[kamea_key])


def traversal_requirements(cells: float = 1.0) -> dict[str, dict[str, float]]:
    """Return the window every classical body needs, for reporting."""
    return {
        key: {
            "bin_degrees": quantization_bin_degrees(key),
            "mean_daily_motion": MEAN_DAILY_MOTION[key],
            "days_per_cell": window_to_traverse(key, cells).total_seconds()
            / 86400.0,
        }
        for key in sorted(CLASSICAL_BODIES)
    }


def _julian_day(moment: datetime) -> float:
    """Return the Julian day for an explicit UTC instant."""
    utc = require_utc(moment)

    hour = (
        utc.hour
        + utc.minute / 60.0
        + utc.second / 3600.0
        + utc.microsecond / 3_600_000_000.0
    )

    return swe.julday(utc.year, utc.month, utc.day, hour)


def body_longitude(moment: datetime, body: str) -> float:
    """Return one body's geocentric longitude at an explicit instant."""
    configure_ephemeris_path(DEFAULT_EPHEMERIS_PATH)

    planets = calculate_planets(_julian_day(moment))
    position = planets.get(body)

    if position is None:
        raise TrajectoryError(
            f"Ephemeris returned no position for {body!r} at "
            f"{moment.isoformat()}."
        )

    return float(position.longitude)


def sample_instants(
    instant: datetime,
    kamea_key: str,
    spec: TrajectorySpec,
) -> tuple[datetime, ...]:
    """Return the chronologically ordered sample times for one body."""
    if kamea_key not in CLASSICAL_BODIES:
        raise TrajectoryError(
            f"{kamea_key!r} has no traditional Kamea. R1 covers the "
            f"classical seven; {', '.join(UNSUPPORTED_BODIES)} are outside "
            "it and must be read from R0."
        )

    moment = require_utc(instant)
    step = spec.step_for(kamea_key)

    return tuple(moment + offset * step for offset in spec.sample_offsets())


def build_trajectory(
    instant: datetime,
    kamea_key: str,
    spec: TrajectorySpec | None = None,
) -> TemporalKameaPath:
    """Build one body's temporal Kamea path around an instant."""
    spec = spec or canonical_spec()
    body = CLASSICAL_BODIES.get(kamea_key)

    if body is None:
        raise TrajectoryError(
            f"{kamea_key!r} has no traditional Kamea. R1 covers the "
            f"classical seven; {', '.join(UNSUPPORTED_BODIES)} are outside "
            "it and must be read from R0."
        )

    instants = sample_instants(instant, kamea_key, spec)
    longitudes = tuple(body_longitude(moment, body) for moment in instants)
    values = tuple(
        quantize_longitude(longitude, kamea_key) for longitude in longitudes
    )

    square = KAMEAS[kamea_key]
    path = square.project_values(
        list(values), use_planetary_transform=spec.use_planetary_transform
    )

    return TemporalKameaPath(
        kamea_key=kamea_key,
        body=body,
        spec=spec,
        instants=instants,
        longitudes=longitudes,
        values=values,
        path=path,
    )


def build_all_trajectories(
    instant: datetime,
    spec: TrajectorySpec | None = None,
) -> dict[str, TemporalKameaPath]:
    """Build every classical body's trajectory around one instant.

    R1 in full: seven independent paths, each on its own square. They are
    returned keyed by Kamea rather than as a concatenated vector, because
    concatenation is a serialization concern and would reintroduce exactly
    the body ordering this representation exists to avoid.
    """
    return {
        key: build_trajectory(instant, key, spec)
        for key in sorted(CLASSICAL_BODIES)
    }


# ---------------------------------------------------------------------------
# Path stability -- the invariant that replaced pointwise continuity
# ---------------------------------------------------------------------------


def _positional_agreement(
    left: Sequence[Any], right: Sequence[Any]
) -> float:
    """Return the fraction of positions holding equal entries."""
    if not left or len(left) != len(right):
        return 0.0

    matched = sum(1 for a, b in zip(left, right) if a == b)

    return matched / len(left)


def _jaccard(left: Iterable[Any], right: Iterable[Any]) -> float:
    """Return the Jaccard overlap of two collections treated as sets."""
    first, second = set(left), set(right)
    union = first | second

    if not union:
        return 1.0

    return len(first & second) / len(union)


def path_similarity(
    left: TemporalKameaPath, right: TemporalKameaPath
) -> dict[str, float]:
    """Compare two trajectories at four levels of the pipeline.

    Reported separately and deliberately so, because they answer different
    questions. Positional agreement on integers and coordinates measures
    whether the same path was produced; occupancy overlap ignores order, so
    it measures whether the same region was visited; core-geometry overlap
    ignores dwell as well, so it measures whether the same shape was drawn.

    Together they say whether reduction *absorbs* cell-level discontinuity or
    merely hides it: if coordinate agreement collapses while core geometry
    holds, the shape is the stable object and the path is not.
    """
    if left.kamea_key != right.kamea_key:
        raise TrajectoryError(
            "Trajectories on different squares are not comparable: "
            f"{left.kamea_key!r} against {right.kamea_key!r}."
        )

    left_occupancy = left.occupancy
    right_occupancy = right.occupancy

    shared = sum(
        min(left_occupancy.get(value, 0), right_occupancy.get(value, 0))
        for value in set(left_occupancy) | set(right_occupancy)
    )
    total = max(sum(left_occupancy.values()), 1)

    return {
        "raw_sequence": _positional_agreement(left.values, right.values),
        "projected_path": _positional_agreement(
            left.coordinates, right.coordinates
        ),
        "reduced_occupancy": shared / total,
        "core_geometry": _jaccard(left.core_geometry, right.core_geometry),
    }


# The perturbations a stability audit applies. Chosen to bracket the
# timestamp precision the event cohorts actually admit: the USGS catalogue
# carries SECOND and MINUTE precision, so the one-minute row is the one that
# decides whether that cohort can be represented at all.
STABILITY_OFFSETS: tuple[tuple[str, timedelta], ...] = (
    ("1_minute", timedelta(minutes=1)),
    ("5_minutes", timedelta(minutes=5)),
    ("30_minutes", timedelta(minutes=30)),
    ("1_hour", timedelta(hours=1)),
    ("1_day", timedelta(days=1)),
)


def representation_occupancy(
    trajectories: Sequence[TemporalKameaPath],
) -> dict[str, Any]:
    """Measure how much of the representation space a body actually uses.

    Distinct from collision rate, and the distinction matters: collisions say
    whether *different inputs* map together, occupancy says how much of the
    space is reached at all. A body could have few collisions while still
    only ever producing a handful of shapes, and that handful is its real
    capacity.

    Reports the dominant core against the long tail, because a distribution
    with a few overwhelming modes and a scatter of singletons behaves very
    differently from a flat one even at identical support size.
    """
    if not trajectories:
        return {"observed": 0}

    shapes: dict[tuple[Any, ...], int] = {}

    for trajectory in trajectories:
        shapes[trajectory.core_shape] = shapes.get(trajectory.core_shape, 0) + 1

    counts = np.array(sorted(shapes.values(), reverse=True), dtype=np.float64)
    frequencies = counts / counts.sum()

    # Shannon entropy of the shape distribution, and its exponential -- the
    # effective number of shapes actually in play, which is far below the
    # nominal support whenever a few dominate.
    entropy = float(-(frequencies * np.log(frequencies)).sum())

    square = KAMEAS[trajectories[0].kamea_key]
    samples = len(trajectories[0].coordinates)

    # Every cell sequence of this length is reachable in principle, so the
    # nominal space is cells^samples. Observed support is always a vanishing
    # fraction of it; the informative quantity is how vanishing.
    nominal = float(square.max_value) ** samples

    return {
        "trajectories": len(trajectories),
        "distinct_core_shapes": len(shapes),
        "effective_support": float(np.exp(entropy)),
        "shape_entropy_nats": entropy,
        "nominal_space_log10": float(np.log10(nominal)),
        "observed_fraction_of_nominal": len(shapes) / nominal,
        "most_common_share": float(frequencies[0]),
        "top_five_share": float(frequencies[:5].sum()),
        "singleton_share": float(
            (counts == 1).sum() / len(counts)
        ),
        "stationary_fraction": sum(
            1 for t in trajectories if t.stationary
        )
        / len(trajectories),
    }


def stability_profile(
    instant: datetime,
    kamea_key: str,
    spec: TrajectorySpec,
    offsets: Sequence[tuple[str, timedelta]] = STABILITY_OFFSETS,
) -> dict[str, dict[str, float]]:
    """Measure how one body's trajectory survives perturbed evaluation times.

    Both directions are applied and averaged, since a representation that is
    stable forwards and unstable backwards is not stable.
    """
    reference = build_trajectory(instant, kamea_key, spec)
    profile: dict[str, dict[str, float]] = {}

    for label, delta in offsets:
        forward = path_similarity(
            reference, build_trajectory(instant + delta, kamea_key, spec)
        )
        backward = path_similarity(
            reference, build_trajectory(instant - delta, kamea_key, spec)
        )

        profile[label] = {
            level: (forward[level] + backward[level]) / 2.0
            for level in forward
        }

    return profile
