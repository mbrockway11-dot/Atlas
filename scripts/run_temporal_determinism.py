"""Temporal Validation 1: deterministic, reproducible temporal representation.

The first temporal milestone deliberately asks nothing about astrology. It
asks whether Atlas can produce temporal representations reproducible enough
that a statistical test of *anything* would mean something.

Acceptance criteria, each checked and reported separately:

    identical state vectors across repeated runs
    deterministic ephemeris versioning
    explicit evaluation instants (naive datetimes refused)
    no placeholder epochs anywhere in the temporal path
    temporal schema hashing
    reproducible historical compilation across a wide date range

Only if all pass does historical statistics become worth running.

    python scripts/run_temporal_determinism.py
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

from atlas.validation.artifacts import write_json
from atlas.validation.temporal_state import (
    ORDERED_BODIES,
    TEMPORAL_SCHEMA_VERSION,
    TEMPORAL_STATE_SCHEMA,
    TemporalStateError,
    build_temporal_matrix,
    build_temporal_state,
    matched_date_controls,
    temporal_feature_layout,
    temporal_schema_hash,
    verify_determinism,
)


# A deliberately wide spread: 19th century through near-future, so
# reproducibility is not established only where the ephemeris is most
# comfortable. All are real, precisely timestamped moments.
REFERENCE_INSTANTS: tuple[tuple[str, datetime], ...] = (
    ("carrington_event", datetime(1859, 9, 1, 11, 18, tzinfo=UTC)),
    ("krakatoa_eruption", datetime(1883, 8, 27, 10, 2, tzinfo=UTC)),
    ("tunguska_event", datetime(1908, 6, 30, 0, 14, tzinfo=UTC)),
    ("trinity_test", datetime(1945, 7, 16, 11, 29, 21, tzinfo=UTC)),
    ("sputnik_launch", datetime(1957, 10, 4, 19, 28, 34, tzinfo=UTC)),
    ("apollo_11_landing", datetime(1969, 7, 20, 20, 17, 40, tzinfo=UTC)),
    ("chernobyl_accident", datetime(1986, 4, 26, 1, 23, 45, tzinfo=UTC)),
    ("tohoku_earthquake", datetime(2011, 3, 11, 5, 46, 24, tzinfo=UTC)),
    ("ligo_first_detection", datetime(2015, 9, 14, 9, 50, 45, tzinfo=UTC)),
    ("future_reference", datetime(2040, 1, 1, 0, 0, tzinfo=UTC)),
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Run Temporal Validation 1 (determinism)."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output") / "validation" / "temporal_determinism_v1",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=5,
        help="Recomputations per instant (default: 5).",
    )
    return parser


def main() -> int:
    """Run the temporal determinism milestone."""
    args = build_parser().parse_args()
    started = perf_counter()

    instants = [instant for _, instant in REFERENCE_INSTANTS]

    checks: dict[str, dict] = {}

    # 1. Repeated runs produce identical states.
    determinism = verify_determinism(instants, repeats=args.repeats)
    checks["identical_across_repeats"] = {
        "passed": determinism["all_stable"],
        "instants": determinism["instants"],
        "repeats": determinism["repeats"],
        "unstable": determinism["unstable"],
    }

    # 2. Ephemeris engine version is recorded and consistent.
    states = [build_temporal_state(instant) for instant in instants]
    engine_versions = {state.ephemeris_engine_version for state in states}
    checks["deterministic_ephemeris_versioning"] = {
        "passed": len(engine_versions) == 1 and all(engine_versions),
        "engine_versions": sorted(engine_versions),
    }

    # 3. Naive datetimes are refused rather than silently localised.
    try:
        build_temporal_state(datetime(2011, 3, 11, 5, 46))
        naive_refused = False
        naive_detail = "A naive datetime was accepted."
    except TemporalStateError as exc:
        naive_refused = True
        naive_detail = str(exc)

    checks["explicit_evaluation_instants"] = {
        "passed": naive_refused,
        "detail": naive_detail,
    }

    # 4. No placeholder epoch appears in a temporal state. The CSS transit
    #    pass uses a fixed placeholder date by design; this path must not.
    placeholder_markers = ("2000-01-01", "1970-01-01")
    serialized = json.dumps([state.to_dict() for state in states])
    checks["no_placeholder_epochs"] = {
        "passed": not any(
            marker in serialized for marker in placeholder_markers
        ),
        "markers_checked": list(placeholder_markers),
        "note": (
            "The CSS temporal pass compiles transits against a fixed "
            "placeholder epoch and labels them placeholder_fixed_epoch. "
            "This path takes explicit instants instead and must never "
            "inherit that."
        ),
    }

    # 5. Temporal schema is hashed and stable.
    schema_hash = temporal_schema_hash()
    checks["temporal_schema_hashing"] = {
        "passed": (
            schema_hash == temporal_schema_hash() and len(schema_hash) == 64
        ),
        "schema": TEMPORAL_STATE_SCHEMA,
        "schema_version": TEMPORAL_SCHEMA_VERSION,
        "schema_hash": schema_hash,
        "dimensions": len(temporal_feature_layout()),
        "bodies": list(ORDERED_BODIES),
    }

    # 6. Historical compilation reproduces across the whole range, and
    #    distinct instants produce distinct states (no silent collapse).
    matrix, _ = build_temporal_matrix(instants)
    repeat_matrix, _ = build_temporal_matrix(instants)

    distinct_states = len({state.content_hash() for state in states})

    checks["reproducible_historical_compilation"] = {
        "passed": bool(
            np.array_equal(matrix, repeat_matrix)
            and distinct_states == len(states)
        ),
        "instants": len(states),
        "distinct_states": distinct_states,
        "matrix_identical_on_recompute": bool(
            np.array_equal(matrix, repeat_matrix)
        ),
        "date_range": [
            min(instants).isoformat(),
            max(instants).isoformat(),
        ],
    }

    # Matched controls, exercised now rather than first used in a
    # substantive study.
    controls = matched_date_controls(instants[-3], count=6, seed=20260801)
    control_matrix, _ = build_temporal_matrix(controls)

    all_passed = all(check["passed"] for check in checks.values())

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        {
            "milestone": "temporal_validation_1_determinism",
            "all_criteria_passed": all_passed,
            "checks": checks,
            "reference_instants": [
                {"label": label, "instant": instant.isoformat()}
                for label, instant in REFERENCE_INSTANTS
            ],
            "matched_control_demo": {
                "event": instants[-3].isoformat(),
                "controls": [c.isoformat() for c in controls],
                "control_states_distinct": int(
                    np.unique(control_matrix, axis=0).shape[0]
                ),
            },
            "note": (
                "This milestone establishes reproducibility only. It makes "
                "no claim about whether temporal structure relates to "
                "events."
            ),
        },
        args.output_dir / "determinism.json",
    )

    print(
        json.dumps(
            {
                "success": True,
                "all_criteria_passed": all_passed,
                "criteria": {
                    name: check["passed"] for name, check in checks.items()
                },
                "schema_hash": schema_hash[:16],
                "dimensions": len(temporal_feature_layout()),
                "instants": len(states),
                "distinct_states": distinct_states,
                "date_range": checks["reproducible_historical_compilation"][
                    "date_range"
                ],
                "output_dir": str(args.output_dir),
                "elapsed_seconds": round(perf_counter() - started, 2),
            },
            indent=2,
        )
    )

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
