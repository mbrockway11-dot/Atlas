"""Temporal 1D: the large-cohort R1-Q audit.

**Cohort design, frozen before running:**

    two independent deterministic irregular cohorts   (seeds fixed below)
    three coprime lattice cadences as aliasing probes (13, 29, 47 days)
    all four canonical scales
    all seven classical bodies
    no event labels of any kind

The job is narrow: determine whether any substantial nondegenerate regime
contradicts quantization dominance. The decision rule is preregistered in
``r1q_classification`` -- it is not derived from what this run shows.

Four translation outcomes are reported separately, because translation can
reduce empirical association without producing a reliable change in held-out
predictability:

    translation_active
    translation_merges_classes
    translation_removes_empirical_era_association
    translation_changes_blocked_era_predictability

    python scripts/run_r1q_large_cohort.py --instants 300

Era labels here are decades, used only to measure what translation does to
era association. No event outcome enters this study.
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
    COPRIME_CADENCE_DAYS,
    encode_cohort,
    irregular_cohort,
    regular_cohort,
)
from atlas.validation.kamea_era import decade_labels
from atlas.validation.r1q_classification import (
    R1Q_SCHEMA,
    build_regime_row,
    classify_r1q,
    robustness_across_cohorts,
)
from atlas.validation.temporal_kamea import (
    CANONICAL_SCALES,
    CLASSICAL_BODIES,
    canonical_spec,
    representation_schema_hash,
)

# Frozen cohort design. Recorded here rather than passed in, so a rerun
# cannot quietly become a different study.
IRREGULAR_SEEDS: tuple[int, ...] = (20260801, 20260902)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Large-cohort R1-Q audit (no events)."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output") / "validation" / "r1q_large_cohort",
    )
    parser.add_argument("--instants", type=int, default=300)
    parser.add_argument(
        "--scales", nargs="*", default=sorted(CANONICAL_SCALES)
    )
    return parser


def main() -> int:
    """Run the large-cohort audit."""
    args = build_parser().parse_args()
    started = perf_counter()

    cohorts: dict[str, list] = {
        f"irregular_{seed}": irregular_cohort(args.instants, seed)
        for seed in IRREGULAR_SEEDS
    }

    # Lattices probe aliasing. Spacing is chosen so the span stays inside
    # the observation window rather than to reach a target size.
    for cadence in COPRIME_CADENCE_DAYS:
        count = min(args.instants, int(55 * 365 / cadence))
        cohorts[f"lattice_{cadence}d"] = regular_cohort(cadence, count)

    rows = []
    scales_payload: dict[str, Any] = {}

    for scale in args.scales:
        spec = canonical_spec(scale)
        scales_payload[scale] = {
            "representation_schema_hash": representation_schema_hash(spec),
        }

        for cohort_name, instants in cohorts.items():
            labels = decade_labels(instants)

            for key in sorted(CLASSICAL_BODIES):
                encodings = encode_cohort(instants, key, spec)
                rows.append(
                    build_regime_row(
                        key, scale, cohort_name, encodings, instants, labels
                    )
                )

    verdict = classify_r1q(rows)
    robustness = robustness_across_cohorts(rows)

    saturated = [
        f"{row.body}/{row.scale}/{row.cohort}"
        for row in rows
        if row.capacity.get("saturated")
    ]

    payload = {
        "study": "temporal_1d_r1q_large_cohort",
        "milestone": "1D_kamea_information_loss_and_scale_audit",
        "schema": R1Q_SCHEMA,
        "study_type": "representation_only",
        "cohort_design": {
            "irregular_seeds": list(IRREGULAR_SEEDS),
            "lattice_cadences_days": list(COPRIME_CADENCE_DAYS),
            "instants_requested": args.instants,
            "cohorts": {
                name: len(instants) for name, instants in cohorts.items()
            },
            "frozen_before_running": True,
        },
        "scales": scales_payload,
        "verdict": verdict,
        "robustness": robustness,
        "saturated_regimes": saturated,
        "rows": [row.to_dict() for row in rows],
    }

    written = write_json(payload, args.output_dir / "r1q_large_cohort.json")

    print(
        json.dumps(
            {
                "success": True,
                "regimes": verdict["regimes"],
                "classification": verdict["classification"],
                "r1q_holds": verdict["r1q_holds"],
                "contradicting_regimes": verdict["contradicting_regimes"],
                "saturated_regimes": len(saturated),
                "translation_stable_across_cohorts": robustness["stable"],
                "unstable": robustness["unstable_across_cohorts"],
                "artifact": str(written),
                "elapsed_seconds": round(perf_counter() - started, 2),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
