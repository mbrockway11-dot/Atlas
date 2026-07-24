"""Temporal 1D: the B0-B3 baseline audit.

Runs the comparison hierarchy on one frozen cohort, with every encoding
derived from the same astronomical states so that differences are
attributable to the arrangement and the reduction rather than to mismatched
inputs:

    B0 -> B1   does temporal traversal add beyond the centre cell?
    B1 -> B2   what does reduction remove, and what equivalence classes
               does it create?
    B2 <-> B3  does Kamea geometry add structure beyond ordinary
               quantization?

B1 and B3 are related by an invertible cell lookup, so they must agree on
every information-theoretic quantity. The audit asserts that rather than
reporting it: a mismatch is a harness fault. It also means B2 versus B3 is
the only place the reduction can show an information effect.

Capacity is reported against stability and compression, never alone. A
maximally discriminative encoding may simply be responding to every
incidental path detail, which is a defect wearing the costume of a result.

    python scripts/run_kamea_baseline_audit.py
    python scripts/run_kamea_baseline_audit.py --instants 200 --all-scales

No event or birth outcome enters this audit.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter
from typing import Any

from atlas.validation.artifacts import write_json
from atlas.validation.kamea_baselines import (
    BASELINE_SCHEMA,
    COPRIME_CADENCE_DAYS,
    ENCODING_DESCRIPTIONS,
    ENCODINGS,
    audit_body,
    cadence_cohorts,
)
from atlas.validation.temporal_kamea import (
    CANONICAL_SCALES,
    CLASSICAL_BODIES,
    canonical_spec,
    representation_schema_hash,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="B0-B3 baseline audit for Temporal 1D (no events)."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output") / "validation" / "kamea_baseline_audit",
    )
    parser.add_argument("--instants", type=int, default=80)
    parser.add_argument("--seed", type=int, default=20260801)
    parser.add_argument(
        "--all-scales",
        action="store_true",
        help="Audit all four canonical scales rather than the extremes.",
    )
    parser.add_argument(
        "--all-cadences",
        action="store_true",
        help="Include every coprime lattice, not just the irregular cohort "
        "and one lattice.",
    )
    return parser


def cadence_agreement(by_cohort: dict[str, Any], body: str) -> dict[str, Any]:
    """Compare occupancy across cohorts to expose lattice artifacts.

    A single regular cadence can alias periodic motion. If the irregular
    cohort and the lattices disagree about effective support, the estimate
    is a property of the sampling rather than of the representation.
    """
    supports = {
        name: cohort[body]["capacity"]["B2"]["effective_support"]
        for name, cohort in by_cohort.items()
    }

    values = list(supports.values())
    spread = (
        (max(values) - min(values)) / max(values) if max(values) > 0 else 0.0
    )

    return {
        "effective_support_by_cohort": supports,
        "relative_spread": spread,
        # Agreement across coprime lattices and an irregular draw is evidence
        # the estimate is not a sampling artifact.
        "consistent_across_cadences": spread < 0.25,
    }


def main() -> int:
    """Run the baseline audit."""
    args = build_parser().parse_args()
    started = perf_counter()

    scales = (
        sorted(CANONICAL_SCALES)
        if args.all_scales
        else ["R1-W3D", "R1-W1Y"]
    )

    cohorts = cadence_cohorts(args.instants, args.seed)

    if not args.all_cadences:
        cohorts = [cohorts[0], cohorts[1]]

    results: dict[str, Any] = {}
    harness_faults: list[str] = []

    for scale in scales:
        spec = canonical_spec(scale)
        by_cohort: dict[str, Any] = {}

        for cohort in cohorts:
            bodies = {
                key: audit_body(cohort, key, spec)
                for key in sorted(CLASSICAL_BODIES)
            }

            for key, body in bodies.items():
                check = body["bijection_check"]

                # B1 and B3 are a relabelling of each other. Disagreement
                # means the encodings were not built from the same states.
                if not check["collision_structure_matches"] or (
                    abs(check["entropy_b1"] - check["entropy_b3"]) > 1e-12
                ):
                    harness_faults.append(
                        f"{scale}/{cohort.name}/{key}: B1 and B3 disagree"
                    )

            by_cohort[cohort.name] = bodies

        results[scale] = {
            "spec": spec.to_dict(),
            "representation_schema_hash": representation_schema_hash(spec),
            "cohorts": {name: c.to_dict() for name, c in zip(
                (cohort.name for cohort in cohorts), cohorts
            )},
            "bodies": by_cohort,
            "cadence_agreement": {
                key: cadence_agreement(by_cohort, key)
                for key in sorted(CLASSICAL_BODIES)
            },
        }

    saturated = [
        f"{scale}/{cohort}/{body}/{encoding}"
        for scale, block in results.items()
        for cohort, bodies in block["bodies"].items()
        for body, payload in bodies.items()
        for encoding in ENCODINGS
        if payload["capacity"][encoding]["saturated"]
    ]

    payload = {
        "study": "temporal_1d_baseline_audit",
        "milestone": "1D_kamea_information_loss_and_scale_audit",
        "schema": BASELINE_SCHEMA,
        "study_type": "representation_only",
        "encodings": ENCODING_DESCRIPTIONS,
        "coprime_cadences_days": list(COPRIME_CADENCE_DAYS),
        "harness_faults": harness_faults,
        "harness_sound": not harness_faults,
        # Reported rather than hidden: a saturated sample measures the
        # cohort, not the representation's capacity.
        "saturated_measurements": saturated,
        "scales": results,
        "interpretation": (
            "B1 and B3 are informationally identical by construction, so "
            "B2 against B3 is the only comparison in which reduction can "
            "show an information effect. Capacity is never read alone: an "
            "encoding can be maximally discriminative because it responds "
            "to every incidental detail."
        ),
    }

    written = write_json(payload, args.output_dir / "baseline_audit.json")

    print(
        json.dumps(
            {
                "success": True,
                "harness_sound": not harness_faults,
                "harness_faults": harness_faults,
                "saturated_measurements": len(saturated),
                "scales": {
                    scale: {
                        body: {
                            "B2_shapes": payload_body["capacity"]["B2"][
                                "observed_signatures"
                            ],
                            "B2_eff": round(
                                payload_body["capacity"]["B2"][
                                    "effective_support"
                                ],
                                2,
                            ),
                            "B3_eff": round(
                                payload_body["capacity"]["B3"][
                                    "effective_support"
                                ],
                                2,
                            ),
                            "collapse": round(
                                payload_body["compression"][
                                    "many_to_one_ratio"
                                ],
                                2,
                            ),
                            "H_kept": round(
                                payload_body["compression"][
                                    "entropy_retained"
                                ],
                                3,
                            ),
                            "stab_B2": round(
                                payload_body["stability"]["B2"], 3
                            ),
                            "measurable": payload_body["capacity"]["B2"][
                                "capacity_measurable"
                            ],
                        }
                        for body, payload_body in block["bodies"][
                            "irregular"
                        ].items()
                    }
                    for scale, block in results.items()
                },
                "artifact": str(written),
                "elapsed_seconds": round(perf_counter() - started, 2),
            },
            indent=2,
        )
    )

    return 0 if not harness_faults else 1


if __name__ == "__main__":
    sys.exit(main())
