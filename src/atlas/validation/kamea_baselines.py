"""B0-B3 baseline encodings for the Temporal 1D audit.

The decisive question is whether the Kamea arrangement and its reduction
contribute structure beyond ordinary quantization. That question is only
answerable if the encodings differ in *nothing else*, so all four are derived
from one shared :class:`TemporalKameaPath` rather than from four pipelines
that happen to agree::

    timestamp cohort
          │
          └── one trajectory per body per instant
                ├── B0  centre Kamea cell
                ├── B1  ordered Kamea path
                ├── B2  reduced / core geometry
                └── B3  ordered quantized longitudes, no square lookup

Same orbit, same timestamps, same quantizer, same sequence length, same square
cardinality. Any difference is attributable to the arrangement and the
reduction.

**A structural check falls out of this.** Cell lookup is a bijection: a
reduced value determines a coordinate and vice versa. So B1 and B3 are
related by a relabelling, and must have *identical* entropy, collision
structure and effective support. They can differ only in geometric
quantities -- distance, shape, adjacency -- which is precisely the content the
square adds. :func:`bijection_check` asserts it, and a violation means the
encodings were fed mismatched inputs rather than that the square did
something interesting.

That also locates the real comparison. B1 versus B3 cannot show an
information difference even in principle, so **B2 versus B3 is where the
reduction has to earn its place.**
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Hashable, Sequence

import numpy as np

from atlas.validation.temporal_kamea import (
    CLASSICAL_BODIES,
    TemporalKameaPath,
    TrajectorySpec,
    build_trajectory,
)


BASELINE_SCHEMA = "atlas.validation.kamea-baselines.v1"

# Ordered so reports read as the audit hierarchy: position, traversal,
# reduction, and the no-geometry control.
ENCODINGS: tuple[str, ...] = ("B0", "B1", "B2", "B3")

ENCODING_DESCRIPTIONS: dict[str, str] = {
    "B0": "centre Kamea cell only -- no path, no order",
    "B1": "ordered sequence of Kamea cells -- path, no reduction",
    "B2": "reduced / core geometry -- the R1 claim",
    "B3": "ordered quantized longitudes -- same bins, no square",
}


def encode_baselines(
    trajectory: TemporalKameaPath,
) -> dict[str, tuple[Hashable, ...]]:
    """Return all four encodings of one trajectory.

    Taking a single trajectory is the matching guarantee: the four encodings
    cannot disagree about window, cadence, body set or quantizer because
    they never independently choose one.
    """
    coordinates = trajectory.coordinates
    centre = len(coordinates) // 2

    return {
        "B0": (coordinates[centre],),
        "B1": coordinates,
        "B2": trajectory.core_shape,
        # The square lookup is the only thing withheld. These are the same
        # integers B1's coordinates were looked up from.
        "B3": trajectory.values,
    }


def bijection_check(
    encodings: Sequence[dict[str, tuple[Hashable, ...]]],
) -> dict[str, Any]:
    """Verify B1 and B3 carry identical information.

    Cell lookup is invertible, so these two encodings are a relabelling of
    each other and must agree on every information-theoretic quantity. This
    is a correctness check on the harness, not a finding: disagreement means
    the encodings were built from mismatched inputs.
    """
    b1 = [item["B1"] for item in encodings]
    b3 = [item["B3"] for item in encodings]

    return {
        "distinct_b1": len(set(b1)),
        "distinct_b3": len(set(b3)),
        "entropy_b1": shannon_entropy(b1),
        "entropy_b3": shannon_entropy(b3),
        "collision_structure_matches": (
            sorted(Counter(b1).values()) == sorted(Counter(b3).values())
        ),
        "note": (
            "B1 and B3 are related by an invertible cell lookup, so any "
            "difference here is a harness fault, not a property of the "
            "square. It also means B2 versus B3 is the only comparison in "
            "which the reduction can show an information effect."
        ),
    }


def shannon_entropy(signatures: Sequence[Hashable]) -> float:
    """Return the entropy of an observed signature distribution, in nats."""
    if not signatures:
        return 0.0

    counts = np.array(list(Counter(signatures).values()), dtype=np.float64)
    frequencies = counts / counts.sum()

    return float(-(frequencies * np.log(frequencies)).sum())


def occupancy_estimates(signatures: Sequence[Hashable]) -> dict[str, Any]:
    """Return support statistics that stay honest under saturation.

    An all-singleton sample cannot support a claim about total support size,
    so the observed count is reported alongside coverage and unseen-mass
    estimates rather than on its own. Chao1 gives a lower bound on richness;
    Good-Turing gives the probability mass sitting on unobserved signatures.
    """
    if not signatures:
        return {"observed_signatures": 0, "samples": 0}

    counts = Counter(signatures)
    frequencies = np.array(list(counts.values()), dtype=np.float64)

    samples = len(signatures)
    observed = len(counts)

    singletons = int((frequencies == 1).sum())
    doubletons = int((frequencies == 2).sum())

    # Chao1: bias-corrected form when no doubletons exist, which is exactly
    # the saturated case where the naive estimator divides by zero.
    if doubletons > 0:
        chao1 = observed + (singletons**2) / (2 * doubletons)
    else:
        chao1 = observed + singletons * (singletons - 1) / 2

    # Good-Turing: the share of mass on unseen signatures. At full
    # saturation every signature is a singleton, coverage collapses to zero,
    # and the estimator says so instead of implying the space was measured.
    unseen_mass = singletons / samples

    entropy = shannon_entropy(signatures)

    return {
        "samples": samples,
        "observed_signatures": observed,
        "singleton_fraction": singletons / observed,
        "effective_support": float(np.exp(entropy)),
        "entropy_nats": entropy,
        "chao1_lower_bound": float(chao1),
        "good_turing_coverage": 1.0 - unseen_mass,
        "estimated_unseen_mass": unseen_mass,
        # The honest verdict. Saturated samples measure the cohort, not the
        # representation, and must not be reported as capacity.
        "saturated": observed == samples,
        "capacity_measurable": observed < samples and unseen_mass < 0.5,
    }


# ---------------------------------------------------------------------------
# Cohorts
# ---------------------------------------------------------------------------

# Reported separately rather than pooled. A single regular cadence can alias
# periodic motion -- particularly for the fast bodies, whose periods are
# comparable to plausible sampling intervals -- so agreement across coprime
# cadences is evidence that an occupancy estimate is not a lattice artifact.
COPRIME_CADENCE_DAYS: tuple[int, ...] = (13, 29, 47)

COHORT_START = datetime(1970, 1, 1, tzinfo=UTC)
COHORT_END = datetime(2025, 12, 31, tzinfo=UTC)


def regular_cohort(
    cadence_days: int,
    count: int,
    start: datetime = COHORT_START,
) -> list[datetime]:
    """Return instants on a fixed lattice."""
    return [start + timedelta(days=cadence_days * index) for index in range(count)]


def irregular_cohort(
    count: int,
    seed: int,
    start: datetime = COHORT_START,
    end: datetime = COHORT_END,
) -> list[datetime]:
    """Return deterministic irregular instants from a frozen seed.

    Irregular by construction, so no periodic motion can beat against the
    sampling; deterministic, so the cohort is reproducible and can be frozen
    with a result.
    """
    rng = np.random.default_rng(seed)
    span = int((end - start).total_seconds())

    return sorted(
        start + timedelta(seconds=int(rng.integers(0, span)))
        for _ in range(count)
    )


@dataclass(frozen=True, slots=True)
class CohortSpec:
    """A named, reproducible set of evaluation instants."""

    name: str
    instants: tuple[datetime, ...]
    kind: str
    detail: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "name": self.name,
            "kind": self.kind,
            "instants": len(self.instants),
            "earliest": min(self.instants).isoformat(),
            "latest": max(self.instants).isoformat(),
            **self.detail,
        }


def cadence_cohorts(count: int, seed: int) -> list[CohortSpec]:
    """Return the irregular cohort plus one per coprime cadence."""
    cohorts = [
        CohortSpec(
            name="irregular",
            instants=tuple(irregular_cohort(count, seed)),
            kind="deterministic_irregular",
            detail={"seed": seed},
        )
    ]

    cohorts.extend(
        CohortSpec(
            name=f"regular_{cadence}d",
            instants=tuple(regular_cohort(cadence, count)),
            kind="regular_lattice",
            detail={"cadence_days": cadence},
        )
        for cadence in COPRIME_CADENCE_DAYS
    )

    return cohorts


# ---------------------------------------------------------------------------
# The audit measurements
# ---------------------------------------------------------------------------


def encode_cohort(
    instants: Sequence[datetime],
    kamea_key: str,
    spec: TrajectorySpec,
) -> list[dict[str, tuple[Hashable, ...]]]:
    """Return every encoding for one body across a cohort."""
    return [
        encode_baselines(build_trajectory(instant, kamea_key, spec))
        for instant in instants
    ]


def capacity_profile(
    encodings: Sequence[dict[str, tuple[Hashable, ...]]],
) -> dict[str, Any]:
    """Return occupancy statistics for each encoding."""
    return {
        name: occupancy_estimates([item[name] for item in encodings])
        for name in ENCODINGS
    }


def compression_profile(
    encodings: Sequence[dict[str, tuple[Hashable, ...]]],
) -> dict[str, Any]:
    """Return what the reduction removes, going B1 to B2.

    Reported as retention rather than as loss: a reduction is *supposed* to
    lose information, so lower entropy is not by itself a defect. What
    matters is the equivalence structure it creates -- how many distinct
    paths collapse into one shape.
    """
    b1 = [item["B1"] for item in encodings]
    b2 = [item["B2"] for item in encodings]

    distinct_b1 = len(set(b1))
    distinct_b2 = len(set(b2))

    entropy_b1 = shannon_entropy(b1)
    entropy_b2 = shannon_entropy(b2)

    # How many distinct paths land in the average shape class.
    collapse = distinct_b1 / distinct_b2 if distinct_b2 else float("nan")

    return {
        "distinct_paths": distinct_b1,
        "distinct_shapes": distinct_b2,
        "many_to_one_ratio": collapse,
        "entropy_retained": (
            entropy_b2 / entropy_b1 if entropy_b1 > 0 else float("nan")
        ),
        "entropy_b1_nats": entropy_b1,
        "entropy_b2_nats": entropy_b2,
    }


def stability_by_encoding(
    instants: Sequence[datetime],
    kamea_key: str,
    spec: TrajectorySpec,
    shift: timedelta = timedelta(minutes=1),
) -> dict[str, float]:
    """Return the fraction of instants whose encoding survives a shift.

    One number per encoding, so capacity and stability can be read against
    each other. A representation that is maximally discriminative because it
    responds to every incidental detail will show it here.
    """
    survived = {name: 0 for name in ENCODINGS}

    for instant in instants:
        reference = encode_baselines(
            build_trajectory(instant, kamea_key, spec)
        )
        shifted = encode_baselines(
            build_trajectory(instant + shift, kamea_key, spec)
        )

        for name in ENCODINGS:
            if reference[name] == shifted[name]:
                survived[name] += 1

    return {
        name: survived[name] / len(instants) for name in ENCODINGS
    }


def audit_body(
    cohort: CohortSpec,
    kamea_key: str,
    spec: TrajectorySpec,
) -> dict[str, Any]:
    """Run the capacity, compression and stability suite for one body."""
    encodings = encode_cohort(cohort.instants, kamea_key, spec)

    return {
        "body": CLASSICAL_BODIES[kamea_key],
        "capacity": capacity_profile(encodings),
        "compression": compression_profile(encodings),
        "stability": stability_by_encoding(
            cohort.instants, kamea_key, spec
        ),
        "bijection_check": bijection_check(encodings),
    }
