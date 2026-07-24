"""Temporal 1C: compare the two preregistered trajectory-sampling families.

A **representation-only** experiment. No events, no outcomes, no cohort. The
question is whether fixed-time or body-relative sampling produces a usable
object, judged on representation criteria alone:

    determinism            same instant, same path, always
    path stability         nearby instants, similar paths  [primary]
    precision sensitivity  survives the timestamp precision studies admit
    collision rate         distinct instants, distinct paths
    degeneracy             does the path move at all
    redundancy             does it retrace or saturate its square

Deliberately not gated by ``write_temporal_result``. That gate exists so an
*event* result cannot be published without control-quality evidence; this
study has no controls because it has no events, and routing it through the
gate would either weaken the gate or fake a control family to satisfy it.

    python scripts/run_kamea_trajectory_sampling.py

Neither family may be selected by how it performs on earthquakes or births.
If both survive, the choice is deferred to 1D rather than resolved by looking
at an outcome.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import sys
from time import perf_counter
from typing import Any

import numpy as np

from atlas.validation.artifacts import write_json
from atlas.validation.temporal_kamea import (
    CANONICAL_FAMILY,
    CANONICAL_SCALES,
    CLASSICAL_BODIES,
    STABILITY_OFFSETS,
    TRAJECTORY_SCHEMA,
    TRAJECTORY_SPEC_VERSION,
    UNSUPPORTED_BODIES,
    SamplingFamily,
    TrajectorySpec,
    build_trajectory,
    quantization_bin_degrees,
    stability_profile,
    traversal_requirements,
)

# The primary acceptance criterion. A representation whose path changes when
# the timestamp moves by less than the cohort's own precision cannot support
# an event study: the result would track rounding, not the sky.
MINIMUM_ONE_MINUTE_STABILITY = 0.95

# A path that never leaves its starting cell carries no geometry.
MINIMUM_DISTINCT_CELLS = 2.0

# Distinct instants must mostly produce distinct paths, or the representation
# cannot distinguish the events it is given.
MINIMUM_DISTINCT_PATH_RATE = 0.90


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Compare trajectory-sampling families (no events)."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output") / "validation" / "kamea_trajectory_sampling",
    )
    parser.add_argument("--reference-instants", type=int, default=48)
    parser.add_argument("--half-width", type=int, default=6)
    parser.add_argument("--step-hours", type=float, default=6.0)
    parser.add_argument("--angular-step", type=float, default=1.0)
    parser.add_argument("--bin-fraction", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=20260801)
    return parser


def reference_instants(count: int, seed: int) -> list[datetime]:
    """Draw evaluation instants spread across the R0 observation window.

    Random rather than regular: a regular grid could beat against a body's
    period and make a family look more stable than it is.
    """
    rng = np.random.default_rng(seed)
    start = datetime(1970, 1, 1, tzinfo=UTC)
    span = int((datetime(2025, 12, 31, tzinfo=UTC) - start).total_seconds())

    return [
        start + timedelta(seconds=int(rng.integers(0, span)))
        for _ in range(count)
    ]


def evaluate_family(
    spec: TrajectorySpec, instants: list[datetime]
) -> dict[str, Any]:
    """Measure one sampling family across every classical body."""
    bodies: dict[str, Any] = {}

    for key in sorted(CLASSICAL_BODIES):
        profiles = [
            stability_profile(instant, key, spec) for instant in instants
        ]

        stability = {
            label: {
                level: float(
                    np.mean([profile[label][level] for profile in profiles])
                )
                for level in ("raw_sequence", "projected_path",
                              "reduced_occupancy", "core_geometry")
            }
            for label, _ in STABILITY_OFFSETS
        }

        trajectories = [
            build_trajectory(instant, key, spec) for instant in instants
        ]

        signatures = {t.coordinates for t in trajectories}
        distinct_cells = [len(set(t.coordinates)) for t in trajectories]
        spans = [t.angular_span_degrees for t in trajectories]
        reversals = [t.reversals for t in trajectories]

        # Determinism is asserted here rather than assumed: the whole
        # temporal branch rests on it, and it costs one rebuild to check.
        deterministic = all(
            build_trajectory(instant, key, spec).coordinates == t.coordinates
            for instant, t in zip(instants, trajectories)
        )

        bodies[key] = {
            "body": CLASSICAL_BODIES[key],
            "step_seconds": spec.step_for(key).total_seconds(),
            "window_days": (
                spec.step_for(key).total_seconds()
                * 2
                * spec.half_width
                / 86400.0
            ),
            "quantization_bin_degrees": quantization_bin_degrees(key),
            "deterministic": deterministic,
            "stability": stability,
            "distinct_path_rate": len(signatures) / len(trajectories),
            "mean_distinct_cells": float(np.mean(distinct_cells)),
            "mean_angular_span_degrees": float(np.mean(spans)),
            "mean_reversals": float(np.mean(reversals)),
        }

    return bodies


def verdict_for(bodies: dict[str, Any]) -> dict[str, Any]:
    """Apply the preregistered acceptance criteria."""
    failures: dict[str, list[str]] = {}

    for key, body in bodies.items():
        problems: list[str] = []

        if not body["deterministic"]:
            problems.append("non_deterministic")

        one_minute = body["stability"]["1_minute"]["projected_path"]

        if one_minute < MINIMUM_ONE_MINUTE_STABILITY:
            problems.append("unstable_at_one_minute")

        if body["mean_distinct_cells"] < MINIMUM_DISTINCT_CELLS:
            problems.append("degenerate_path")

        if body["distinct_path_rate"] < MINIMUM_DISTINCT_PATH_RATE:
            problems.append("excessive_path_collisions")

        if problems:
            failures[key] = problems

    return {
        "acceptable": not failures,
        "failing_bodies": failures,
        "criteria": {
            "minimum_one_minute_stability": MINIMUM_ONE_MINUTE_STABILITY,
            "minimum_distinct_cells": MINIMUM_DISTINCT_CELLS,
            "minimum_distinct_path_rate": MINIMUM_DISTINCT_PATH_RATE,
        },
    }


def main() -> int:
    """Run the sampling-family comparison."""
    args = build_parser().parse_args()
    started = perf_counter()

    instants = reference_instants(args.reference_instants, args.seed)

    specs = {
        SamplingFamily.FIXED_TIME: TrajectorySpec(
            family=SamplingFamily.FIXED_TIME,
            half_width=args.half_width,
            step=timedelta(hours=args.step_hours),
        ),
        SamplingFamily.BODY_RELATIVE: TrajectorySpec(
            family=SamplingFamily.BODY_RELATIVE,
            half_width=args.half_width,
            angular_step_degrees=args.angular_step,
        ),
        SamplingFamily.BIN_RELATIVE: TrajectorySpec(
            family=SamplingFamily.BIN_RELATIVE,
            half_width=args.half_width,
            bin_fraction=args.bin_fraction,
        ),
    }

    families: dict[str, Any] = {}

    for family, spec in specs.items():
        bodies = evaluate_family(spec, instants)

        families[family.value] = {
            "spec": spec.to_dict(),
            "spec_hash": spec.spec_hash(),
            "bodies": bodies,
            "verdict": verdict_for(bodies),
        }

    acceptable = [
        name for name, body in families.items() if body["verdict"]["acceptable"]
    ]

    payload = {
        "study": "temporal_1c_trajectory_sampling",
        "milestone": "1C_planetary_to_kamea_specification",
        "schema": TRAJECTORY_SCHEMA,
        "spec_version": TRAJECTORY_SPEC_VERSION,
        "study_type": "representation_only",
        "reference_instants": len(instants),
        "window": {
            "earliest": min(instants).isoformat(),
            "latest": max(instants).isoformat(),
        },
        "scope": {
            "supported": sorted(CLASSICAL_BODIES.values()),
            "unsupported": list(UNSUPPORTED_BODIES),
            "note": (
                "R1 covers the classical seven. R2 is complete R0 for all ten "
                "bodies plus R1 geometry for the seven. Nothing is silently "
                "omitted."
            ),
        },
        "acceptable_families": acceptable,
        # The structural constraint behind every degeneracy failure below.
        # A body only leaves its starting cell after crossing one bin, and
        # the tradition pairs the slowest body with the coarsest square.
        "traversal_requirements": traversal_requirements(),
        "decision": {
            "canonical_family": CANONICAL_FAMILY.value,
            "canonical_scales": sorted(CANONICAL_SCALES),
            "resolution": "accept_static_slow_bodies",
            "finding": (
                "A temporally local, traditional, planet-native Kamea path "
                "cannot simultaneously provide high discrimination for slow "
                "bodies. Rescuing both would require changing 'local', "
                "'traditional' or 'planet-native'."
            ),
            "rejected_as_canonical": {
                SamplingFamily.BODY_RELATIVE.value: (
                    "Solves occupancy by giving each body its own window, so "
                    "the seven paths stop being observations of the same "
                    "temporal neighbourhood. Retained as R1b, a "
                    "characterization contrast."
                ),
                SamplingFamily.BIN_RELATIVE.value: (
                    "Same loss of contemporaneity, more extreme: Saturn's "
                    "window reaches 7,164 days. Retained as a diagnostic "
                    "that quantifies the tension, not as a mapping."
                ),
            },
            "quantizer_unchanged": (
                "Refining the bins for slow bodies would introduce a "
                "non-traditional square resolution while keeping traditional "
                "labels. That is R1c, and it needs its own symbolic "
                "justification -- it may not be adopted to repair an "
                "unfavourable measurement."
            ),
        },
        "families": families,
        "selection_constraint": (
            "No event or birth outcome entered this comparison. If both "
            "families are acceptable the choice is deferred to 1D, not "
            "resolved by looking at an outcome."
        ),
    }

    written = write_json(
        payload, args.output_dir / "trajectory_sampling.json"
    )

    print(
        json.dumps(
            {
                "success": True,
                "acceptable_families": acceptable,
                "families": {
                    name: {
                        "verdict": body["verdict"]["acceptable"],
                        "failing_bodies": body["verdict"]["failing_bodies"],
                        "bodies": {
                            key: {
                                "window_days": round(b["window_days"], 3),
                                "bin_deg": round(
                                    b["quantization_bin_degrees"], 2
                                ),
                                "stab_1min": round(
                                    b["stability"]["1_minute"][
                                        "projected_path"
                                    ],
                                    3,
                                ),
                                "stab_1day": round(
                                    b["stability"]["1_day"]["projected_path"],
                                    3,
                                ),
                                "core_1day": round(
                                    b["stability"]["1_day"]["core_geometry"],
                                    3,
                                ),
                                "cells": round(b["mean_distinct_cells"], 2),
                                "span_deg": round(
                                    b["mean_angular_span_degrees"], 2
                                ),
                                "distinct": round(b["distinct_path_rate"], 3),
                            }
                            for key, b in body["bodies"].items()
                        },
                    }
                    for name, body in families.items()
                },
                "artifact": str(written),
                "elapsed_seconds": round(perf_counter() - started, 2),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
