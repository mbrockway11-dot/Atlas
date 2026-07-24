"""Temporal Validation 1B (partial): audit of the raw astronomical state R0.

The full 1B design compares three representations -- R0 raw, R1 Kamea-only,
R2 combined. **R1 and R2 cannot currently be built: Atlas has no Kamea
representation of planetary state.** Every call site of
``project_values_to_kamea`` feeds it name-derived cipher values, and no
temporal module imports the Kamea subsystem at all. Constructing the mapping
here would mean auditing an invention of this script rather than an existing
Atlas transform.

What *is* well defined without Kamea is the R0 half of the audit, and it is
prerequisite to any event study regardless of what mapping is later chosen:

    redundancy and effective dimensionality
    local continuity in time
    stability under timestamp uncertainty

The last two matter most for the earthquake cohort. A representation that
changes sharply across a one-minute boundary will manufacture fragile
"significant" results whenever event times are uncertain, and catalogue
timestamps always are.

    python scripts/run_temporal_representation_audit.py --preset development
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

from atlas.validation.artifacts import write_json
from atlas.validation.temporal_state import (
    PANEL_PRESETS,
    build_temporal_matrix,
    build_temporal_state,
    panel_from_preset,
    temporal_feature_layout,
    temporal_schema_hash,
)


# Offsets used for both continuity and timestamp-sensitivity analysis.
OFFSETS: tuple[tuple[str, timedelta], ...] = (
    ("1_minute", timedelta(minutes=1)),
    ("5_minutes", timedelta(minutes=5)),
    ("30_minutes", timedelta(minutes=30)),
    ("1_hour", timedelta(hours=1)),
    ("6_hours", timedelta(hours=6)),
    ("1_day", timedelta(days=1)),
)

# A feature is called stable at an offset when its median absolute change is
# below this share of its own spread across the panel.
STABLE_THRESHOLD = 0.01
MODERATE_THRESHOLD = 0.10


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Audit the raw temporal representation (R0)."
    )
    parser.add_argument(
        "--preset",
        default="development",
        choices=sorted(PANEL_PRESETS),
        help="Panel size (default: development).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output")
        / "validation"
        / "temporal_representation_audit_v1",
    )
    parser.add_argument(
        "--random-samples",
        type=int,
        default=500,
        help="Seeded random instants added to the regular cadence.",
    )
    parser.add_argument(
        "--continuity-sample",
        type=int,
        default=400,
        help="Instants used for continuity and sensitivity (default: 400).",
    )
    parser.add_argument("--seed", type=int, default=20260801)
    return parser


def effective_dimension(matrix: np.ndarray) -> dict:
    """Return PCA-based and participation-ratio dimensionality."""
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    deviations = centered.std(axis=0, keepdims=True)
    scaled = centered / np.where(deviations == 0.0, 1.0, deviations)

    # Eigenvalues of the correlation matrix, via SVD for stability.
    singular = np.linalg.svd(scaled, compute_uv=False)
    eigenvalues = (singular**2) / max(scaled.shape[0] - 1, 1)
    total = float(eigenvalues.sum())

    if total <= 0:
        return {"nominal_dimension": int(matrix.shape[1])}

    ratios = np.cumsum(eigenvalues) / total

    def components_for(share: float) -> int:
        return int(np.searchsorted(ratios, share) + 1)

    participation = float(
        (eigenvalues.sum() ** 2) / float((eigenvalues**2).sum())
    )

    condition = (
        float(singular.max() / singular.min())
        if singular.min() > 0
        else float("inf")
    )

    return {
        "nominal_dimension": int(matrix.shape[1]),
        "components_90pct": components_for(0.90),
        "components_95pct": components_for(0.95),
        "components_99pct": components_for(0.99),
        "participation_ratio": participation,
        "condition_number": condition,
        "top_eigenvalue_share": float(eigenvalues[0] / total),
    }


def redundancy(matrix: np.ndarray, layout: tuple[str, ...]) -> dict:
    """Return duplicate and near-duplicate column statistics."""
    deviations = matrix.std(axis=0)
    constant = [
        layout[index]
        for index in range(matrix.shape[1])
        if deviations[index] == 0.0
    ]

    varying = np.flatnonzero(deviations > 0)
    correlations = np.corrcoef(matrix[:, varying], rowvar=False)
    np.fill_diagonal(correlations, 0.0)

    absolute = np.abs(correlations)
    rows, columns = np.triu_indices(absolute.shape[0], k=1)
    pairs = absolute[rows, columns]

    def count_above(threshold: float) -> int:
        return int(np.count_nonzero(pairs >= threshold))

    strongest = np.argsort(pairs)[::-1][:15]

    return {
        "constant_columns": len(constant),
        "constant_column_names": constant[:10],
        "varying_columns": int(varying.size),
        "mean_absolute_correlation": float(pairs.mean()),
        "pairs_above_0.99": count_above(0.99),
        "pairs_above_0.95": count_above(0.95),
        "pairs_above_0.90": count_above(0.90),
        "strongest_pairs": [
            {
                "a": layout[int(varying[rows[index]])],
                "b": layout[int(varying[columns[index]])],
                "abs_correlation": float(pairs[index]),
            }
            for index in strongest
        ],
    }


def continuity_and_sensitivity(
    instants: list[datetime],
    layout: tuple[str, ...],
    panel_scale: np.ndarray,
) -> tuple[dict, dict]:
    """Return local continuity and per-feature timestamp sensitivity."""
    base_matrix, _ = build_temporal_matrix(instants)

    continuity: dict[str, dict] = {}
    sensitivity: dict[str, dict] = {}

    for label, offset in OFFSETS:
        shifted_matrix, _ = build_temporal_matrix(
            [moment + offset for moment in instants]
        )

        deltas = np.abs(shifted_matrix - base_matrix)

        # Whole-state distance, in units of the panel's own spread, so
        # features on different scales contribute comparably.
        scaled = deltas / panel_scale
        distances = np.linalg.norm(scaled, axis=1)

        continuity[label] = {
            "median_distance": float(np.median(distances)),
            "p90_distance": float(np.percentile(distances, 90)),
            "max_distance": float(distances.max()),
            # A jump far beyond the typical one indicates a discontinuity
            # rather than smooth motion.
            "discontinuity_ratio": (
                float(distances.max() / np.median(distances))
                if np.median(distances) > 0
                else float("inf")
            ),
        }

        median_change = np.median(deltas, axis=0) / panel_scale

        classified = {
            "stable": [],
            "moderately_sensitive": [],
            "highly_sensitive": [],
        }

        for index, change in enumerate(median_change):
            if change < STABLE_THRESHOLD:
                classified["stable"].append(layout[index])
            elif change < MODERATE_THRESHOLD:
                classified["moderately_sensitive"].append(layout[index])
            else:
                classified["highly_sensitive"].append(layout[index])

        sensitivity[label] = {
            "stable": len(classified["stable"]),
            "moderately_sensitive": len(classified["moderately_sensitive"]),
            "highly_sensitive": len(classified["highly_sensitive"]),
            "highly_sensitive_features": classified["highly_sensitive"][:15],
            "median_relative_change": float(np.median(median_change)),
        }

    return continuity, sensitivity


def collision_analysis(matrix: np.ndarray, instants: list[datetime]) -> dict:
    """Return exact and near collisions in the raw representation.

    Operates on the state values only. An earlier version compared
    ``content_hash``, which includes the instant and therefore made every
    state unique by construction -- it could not have found a collision even
    if one existed.
    """
    rounded = np.round(matrix, 9)
    _, inverse, counts = np.unique(
        rounded, axis=0, return_inverse=True, return_counts=True
    )

    duplicate_groups = int(np.count_nonzero(counts > 1))

    return {
        "states": int(matrix.shape[0]),
        "distinct_states": int(counts.size),
        "exact_collision_groups": duplicate_groups,
        "largest_group": int(counts.max()),
        "note": (
            "Exact collisions in R0 would indicate a defect: distinct "
            "instants should not produce identical planetary states."
        ),
    }


def main() -> int:
    """Run the R0 audit."""
    args = build_parser().parse_args()
    started = perf_counter()

    layout = temporal_feature_layout()

    panel = panel_from_preset(
        args.preset,
        random_samples=args.random_samples,
        seed=args.seed,
    )

    matrix, _ = build_temporal_matrix(panel)

    # Per-feature spread across the panel, used to make changes comparable.
    panel_scale = matrix.std(axis=0)
    panel_scale = np.where(panel_scale == 0.0, 1.0, panel_scale)

    rng = np.random.default_rng(args.seed)
    sample_size = min(args.continuity_sample, len(panel))
    sample_rows = rng.choice(len(panel), size=sample_size, replace=False)
    sample_instants = [panel[int(index)] for index in sample_rows]

    continuity, sensitivity = continuity_and_sensitivity(
        sample_instants, layout, panel_scale
    )

    report = {
        "milestone": "temporal_validation_1b_partial_r0_audit",
        "blocked": {
            "r1_kamea_only": "no Kamea representation of planetary state exists",
            "r2_combined": "depends on R1",
            "detail": (
                "Every project_values_to_kamea call site passes name-derived "
                "cipher values (essence/builder, invariant/pipeline, "
                "profiles/summary, kamea/identity_graph). No temporal module "
                "imports the Kamea subsystem. Defining the mapping here "
                "would audit this script's invention rather than an Atlas "
                "transform."
            ),
        },
        "panel": {
            "preset": args.preset,
            "instants": len(panel),
            "regular_cadence_hours": PANEL_PRESETS[args.preset][
                "cadence_hours"
            ],
            "random_samples": args.random_samples,
            "range": [min(panel).isoformat(), max(panel).isoformat()],
            "seed": args.seed,
        },
        "schema": {
            "hash": temporal_schema_hash(),
            "dimensions": len(layout),
        },
        "effective_dimension": effective_dimension(matrix),
        "redundancy": redundancy(matrix, layout),
        "collisions": collision_analysis(matrix, panel),
        "local_continuity": continuity,
        "timestamp_sensitivity": sensitivity,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(report, args.output_dir / "r0_audit.json")

    effective = report["effective_dimension"]

    print(
        json.dumps(
            {
                "success": True,
                "r1_r2_blocked": True,
                "panel_instants": len(panel),
                "nominal_dimensions": effective["nominal_dimension"],
                "effective_dimension": {
                    "components_90pct": effective["components_90pct"],
                    "components_95pct": effective["components_95pct"],
                    "components_99pct": effective["components_99pct"],
                    "participation_ratio": round(
                        effective["participation_ratio"], 2
                    ),
                },
                "redundancy": {
                    "pairs_above_0.99": report["redundancy"][
                        "pairs_above_0.99"
                    ],
                    "pairs_above_0.95": report["redundancy"][
                        "pairs_above_0.95"
                    ],
                    "constant_columns": report["redundancy"][
                        "constant_columns"
                    ],
                },
                "collisions": {
                    "distinct_states": report["collisions"][
                        "distinct_states"
                    ],
                    "exact_collision_groups": report["collisions"][
                        "exact_collision_groups"
                    ],
                },
                "timestamp_sensitivity": {
                    label: {
                        "stable": body["stable"],
                        "moderate": body["moderately_sensitive"],
                        "high": body["highly_sensitive"],
                    }
                    for label, body in sensitivity.items()
                },
                "continuity_median_distance": {
                    label: round(body["median_distance"], 5)
                    for label, body in continuity.items()
                },
                "output_dir": str(args.output_dir),
                "elapsed_seconds": round(perf_counter() - started, 2),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
