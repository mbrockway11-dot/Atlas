"""Temporal 1D: prove an R1 control generator can produce valid cohorts.

The gate in ``r1_control_quality`` can reject a masked cohort. This proves an
acceptable one is constructible -- otherwise the refusal boundary is one that
nothing can pass.

A generator must remove **representation-level separability**: Saturn's B3D
classes must stop distinguishing events from controls. Matching calendar-year
histograms is not sufficient evidence, because the histogram is the presumed
cause and the separability is the effect actually at issue.

The inadequate baseline is included deliberately. A proof in which every
candidate passes shows only that the gate is inert.

    python scripts/run_r1_control_generator_proof.py

No event outcome enters this study.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter
from typing import Any

from atlas.validation.artifacts import write_json
from atlas.validation.r1_control_generators import (
    ERA_CONTRASTS,
    EXPECTED_INADEQUATE,
    GENERATOR_SCHEMA,
    GENERATORS,
    prove_generator,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Prove an R1 control generator (no events)."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output") / "validation" / "r1_control_generators",
    )
    parser.add_argument("--events", type=int, default=50)
    parser.add_argument("--per-event", type=int, default=2)
    parser.add_argument("--permutations", type=int, default=60)
    parser.add_argument(
        "--scales", nargs="*", default=["R1-W3D", "R1-W1Y"]
    )
    return parser


def main() -> int:
    """Run the generator proof."""
    args = build_parser().parse_args()
    started = perf_counter()

    proofs: dict[str, Any] = {}

    for name in GENERATORS:
        proofs[name] = prove_generator(
            name,
            scales=tuple(args.scales),
            events=args.events,
            per_event=args.per_event,
            permutations=args.permutations,
        )

    acceptable = [
        name
        for name, proof in proofs.items()
        if proof["acceptable_everywhere"]
    ]

    # The gate must reject something, or it is proving nothing.
    discriminates = any(
        not proofs[name]["acceptable_everywhere"]
        for name in EXPECTED_INADEQUATE
    )

    # Canonical choice: the simplest generator that passes without matching
    # on the representation itself, since doing so conditions away the
    # feature under study.
    canonical = next(
        (
            name
            for name in ("stratified_era", "symmetric_displacement")
            if name in acceptable
        ),
        None,
    )

    payload = {
        "study": "temporal_1d_control_generator_proof",
        "milestone": "1D_kamea_information_loss_and_scale_audit",
        "schema": GENERATOR_SCHEMA,
        "study_type": "representation_only",
        "contrasts": sorted(ERA_CONTRASTS),
        "scales": list(args.scales),
        "gate_discriminates": discriminates,
        "acceptable_generators": acceptable,
        "canonical_generator": canonical,
        "canonical_rationale": (
            "The simplest generator that removes Saturn's B3D separability "
            "without matching on the representation. Representation matching "
            "also works, but conditions away the feature under study and so "
            "changes the estimand -- it is a diagnostic upper bound, not a "
            "canonical choice."
        ),
        "proofs": proofs,
    }

    written = write_json(payload, args.output_dir / "generator_proof.json")

    print(
        json.dumps(
            {
                "success": True,
                "gate_discriminates": discriminates,
                "acceptable_generators": acceptable,
                "canonical_generator": canonical,
                "summary": {
                    name: {
                        "conditions": proof["conditions"],
                        "acceptable_everywhere": proof[
                            "acceptable_everywhere"
                        ],
                        "failures": len(proof["failing_conditions"]),
                        "expected_inadequate": proof["expected_inadequate"],
                    }
                    for name, proof in proofs.items()
                },
                "artifact": str(written),
                "elapsed_seconds": round(perf_counter() - started, 2),
            },
            indent=2,
        )
    )

    return 0 if discriminates and canonical else 1


if __name__ == "__main__":
    sys.exit(main())
