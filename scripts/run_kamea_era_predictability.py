"""Temporal 1D: blocked era predictability across B3, B3D and B2.

Runs before any R1 event study, because accepting static slow bodies made a
static cell an era marker and that is Temporal 2 v1's failure in R1 form.

The partition decomposition localizes the leakage rather than merely
detecting it::

    B3    quantized orbital state
    B3D   after repeat removal        -> dedup's contribution
    B2    after translation           -> the square's contribution

Mutual information and blocked accuracy are reported separately and must not
be collapsed. B2 is a coarsening of B3D, so it cannot add population
information; if accuracy rises while information falls, that is regularization
from merging classes.

Validation is blocked by calendar year. A random split would put adjacent
timestamps, with effectively identical slow-body state, in both train and
test.

    python scripts/run_kamea_era_predictability.py

No event outcome enters this study.
"""

from __future__ import annotations

import argparse
from datetime import timedelta
import json
from pathlib import Path
import sys
from time import perf_counter
from typing import Any

import numpy as np

from atlas.validation.artifacts import write_json
from atlas.validation.kamea_baselines import encode_cohort
from atlas.validation.kamea_era import (
    EARLY_ERA,
    ERA_SCHEMA,
    LATE_ERA,
    binary_era_labels,
    era_decomposition,
)
from atlas.validation.temporal_kamea import (
    CLASSICAL_BODIES,
    canonical_spec,
    representation_schema_hash,
)

# Any body whose encoding separates well-separated decades this reliably is
# carrying era, and event/control balance must be checked in R1 space before
# it is used.
ERA_LEAKAGE_ACCURACY = 0.70


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Blocked era predictability for R1 encodings."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output") / "validation" / "kamea_era",
    )
    parser.add_argument("--per-era", type=int, default=60)
    parser.add_argument("--folds", type=int, default=4)
    parser.add_argument("--permutations", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260801)
    parser.add_argument(
        "--scales", nargs="*", default=["R1-W3D", "R1-W1Y"]
    )
    return parser


def draw_cohort(per_era: int, seed: int) -> list:
    """Draw a deterministic cohort inside the two declared eras."""
    rng = np.random.default_rng(seed)

    instants = []

    for start, end in (EARLY_ERA, LATE_ERA):
        span = int((end - start).total_seconds())
        instants.extend(
            start + timedelta(seconds=int(rng.integers(0, span)))
            for _ in range(per_era)
        )

    return sorted(instants)


def main() -> int:
    """Run the era-predictability decomposition."""
    args = build_parser().parse_args()
    started = perf_counter()

    instants, labels = binary_era_labels(
        draw_cohort(args.per_era, args.seed)
    )

    scales: dict[str, Any] = {}
    leaking: list[str] = []
    anomalies: list[str] = []

    for scale in args.scales:
        spec = canonical_spec(scale)
        bodies: dict[str, Any] = {}

        for key in sorted(CLASSICAL_BODIES):
            encodings = encode_cohort(instants, key, spec)
            decomposition = era_decomposition(
                encodings,
                instants,
                labels,
                folds=args.folds,
                permutations=args.permutations,
                seed=args.seed,
            )

            for name, block in decomposition["encodings"].items():
                if block["balanced_accuracy"] >= ERA_LEAKAGE_ACCURACY:
                    leaking.append(f"{scale}/{key}/{name}")

            # A coarsening cannot add population information. If it appears
            # to, the harness is at fault, not the square.
            if decomposition["translation_added_information"]:
                anomalies.append(f"{scale}/{key}: B2 information exceeds B3D")

            bodies[key] = decomposition

        scales[scale] = {
            "representation_schema_hash": representation_schema_hash(spec),
            "bodies": bodies,
        }

    payload = {
        "study": "temporal_1d_era_predictability",
        "milestone": "1D_kamea_information_loss_and_scale_audit",
        "schema": ERA_SCHEMA,
        "study_type": "representation_only",
        "eras": {
            "early": [EARLY_ERA[0].isoformat(), EARLY_ERA[1].isoformat()],
            "late": [LATE_ERA[0].isoformat(), LATE_ERA[1].isoformat()],
        },
        "cohort": {
            "instants": len(instants),
            "folds": args.folds,
            "validation": "year_blocked",
        },
        "era_leakage_threshold": ERA_LEAKAGE_ACCURACY,
        "leaking_encodings": leaking,
        "harness_anomalies": anomalies,
        "scales": scales,
        "interpretation": (
            "Mutual information and blocked accuracy are distinct. A "
            "coarsening cannot add population information, but merging "
            "classes can raise finite-sample accuracy through "
            "regularization. Any encoding above the leakage threshold "
            "requires event/control balance to be checked in R1 space, not "
            "only in R0 space."
        ),
    }

    written = write_json(payload, args.output_dir / "era_predictability.json")

    print(
        json.dumps(
            {
                "success": True,
                "leaking_encodings": leaking,
                "harness_anomalies": anomalies,
                "scales": {
                    scale: {
                        body: {
                            name: {
                                "mi": round(
                                    block["mutual_information_nats"], 3
                                ),
                                "acc": round(block["balanced_accuracy"], 3),
                                "p": round(block["mi_p_value"], 3),
                                "unseen": round(
                                    block["unseen_class_rate"], 3
                                ),
                            }
                            for name, block in payload_body[
                                "encodings"
                            ].items()
                        }
                        for body, payload_body in block["bodies"].items()
                    }
                    for scale, block in scales.items()
                },
                "artifact": str(written),
                "elapsed_seconds": round(perf_counter() - started, 2),
            },
            indent=2,
        )
    )

    return 0 if not anomalies else 1


if __name__ == "__main__":
    sys.exit(main())
