"""Temporal 2 v2: earthquake baseline with window-confined controls.

Same immutable USGS snapshot, same R0 schema, same endpoint. **Only the
control specification changes**, and it changed before this ran, not after.

v1's two significant results came from its own generators sampling outside
the observation window: 35.7% for matched and 12.6% for uniform, against
0.3% and 0.0% for the two null families. Feature-level diagnostics confirmed
the mechanism -- every one of the top six imbalanced features for both
significant families was an outer-planet component, led by Uranus~Neptune
separation, while the null families' imbalance was an order of magnitude
smaller.

v2 confines every generator to the window by rejection sampling, adds an
era-stratified family that holds slow-planet state nearly fixed by
construction, and reports era balance and feature imbalance for every family
so a repeat of v1's failure would be visible in the result itself.

Three inference levels are reported, because 772 events do not carry 772
independent observations:

    event-level      every event counted separately
    cluster-aware    aftershock sequences as resampling blocks
    year-block       calendar years as blocks, the most conservative

    python scripts/run_earthquake_r0_v2.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter
from typing import Any, Sequence

import numpy as np

from atlas.validation.control_quality import (
    build_control_quality,
    write_temporal_result,
)
from atlas.validation.event_catalogue import (
    CONFIRMATORY_PROVENANCE,
    InclusionRule,
    TimestampPrecision,
    apply_inclusion_rule,
    load_catalogue,
    summarize_catalogue,
)
from atlas.validation.metrics import separation
from atlas.validation.temporal_controls import (
    CONTROL_FAMILIES,
    CONTROL_SPEC_VERSION,
    era_balance,
    feature_imbalance,
    window_from_events,
)
from atlas.validation.temporal_state import (
    build_temporal_matrix,
    temporal_feature_layout,
    temporal_schema_hash,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_earthquake_r0_baseline import (  # noqa: E402
    CLUSTER_RADIUS_KM,
    CLUSTER_WINDOW_DAYS,
    _dispersion,
    assign_clusters,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Temporal 2 v2 with window-confined controls."
    )
    parser.add_argument(
        "--catalogue",
        type=Path,
        default=Path("data") / "validation" / "earthquakes" / "catalogue.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output") / "validation" / "earthquake_r0_v2",
    )
    parser.add_argument("--minimum-magnitude", type=float, default=7.0)
    parser.add_argument("--controls-per-event", type=int, default=20)
    parser.add_argument("--permutations", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=20260801)
    return parser


def _block_permutation(
    events: np.ndarray,
    controls: np.ndarray,
    blocks: Sequence[int],
    *,
    iterations: int,
    seed: int,
) -> dict[str, Any]:
    """Permutation test resampling whole blocks.

    ``blocks`` labels each event. Resampling at block level keeps
    within-block correlation intact, so the null is not tightened by
    counting correlated observations as independent draws.
    """
    if events.size == 0 or controls.size == 0:
        return {"observed_difference": 0.0, "p_value": 1.0, "blocks": 0}

    observed = float(events.mean() - controls.mean())

    grouped: dict[int, list[float]] = {}

    for value, label in zip(events, blocks):
        grouped.setdefault(int(label), []).append(float(value))

    ids = list(grouped)
    pooled = np.concatenate((events, controls))

    rng = np.random.default_rng(seed)
    extreme = 0

    for _ in range(iterations):
        drawn = rng.choice(len(ids), size=len(ids))
        size = sum(len(grouped[ids[int(i)]]) for i in drawn)
        size = min(max(size, 1), pooled.size - 1)

        shuffled = rng.permutation(pooled)
        difference = shuffled[:size].mean() - shuffled[size:].mean()

        if abs(difference) >= abs(observed):
            extreme += 1

    return {
        "observed_difference": observed,
        "p_value": (extreme + 1) / (iterations + 1),
        "iterations": iterations,
        "blocks": len(ids),
    }


def main() -> int:
    """Run the v2 study."""
    args = build_parser().parse_args()
    started = perf_counter()

    records = load_catalogue(args.catalogue)

    rule = InclusionRule(
        event_class="earthquake",
        minimum_magnitude=args.minimum_magnitude,
        required_precision=(
            TimestampPrecision.SECOND,
            TimestampPrecision.MINUTE,
        ),
    )
    filtered = apply_inclusion_rule(records, rule)
    admitted = filtered["admitted"]

    if not all(r.provenance in CONFIRMATORY_PROVENANCE for r in admitted):
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "Catalogue contains non-confirmatory records.",
                },
                indent=2,
            )
        )
        return 1

    events = [record.instant for record in admitted]
    window = window_from_events(events)
    layout = temporal_feature_layout()
    event_matrix, _ = build_temporal_matrix(events)

    clusters = assign_clusters(admitted)
    years = [record.instant.year for record in admitted]

    event_days = {record.instant.date() for record in admitted}
    rng = np.random.default_rng(args.seed)

    results: dict[str, Any] = {}
    controls_by_family: dict[str, list] = {}
    control_matrices: dict[str, np.ndarray] = {}

    for family, generator in CONTROL_FAMILIES.items():
        drawn: list = []

        for event in events:
            drawn.extend(
                generator(
                    event,
                    count=args.controls_per_event,
                    window=window,
                    rng=rng,
                )
            )

        kept = [moment for moment in drawn if moment.date() not in event_days]
        control_matrix, _ = build_temporal_matrix(kept)

        controls_by_family[family] = kept
        control_matrices[family] = control_matrix

        combined = np.vstack((event_matrix, control_matrix))
        dispersion = _dispersion(combined)

        events_part = dispersion[: event_matrix.shape[0]]
        controls_part = dispersion[event_matrix.shape[0] :]

        balance = era_balance(events, kept, window)

        results[family] = {
            "controls_drawn": len(drawn),
            "controls_after_event_exclusion": len(kept),
            "collisions_with_cohort_events": len(drawn) - len(kept),
            "era_balance": balance,
            "feature_imbalance": feature_imbalance(
                event_matrix, control_matrix, layout
            ),
            "event_mean_dispersion": float(events_part.mean()),
            "control_mean_dispersion": float(controls_part.mean()),
            **separation(events_part, controls_part),
            "inference": {
                "event_level": _block_permutation(
                    events_part,
                    controls_part,
                    list(range(len(events))),
                    iterations=args.permutations,
                    seed=args.seed,
                ),
                "cluster_aware": _block_permutation(
                    events_part,
                    controls_part,
                    clusters,
                    iterations=args.permutations,
                    seed=args.seed,
                ),
                "year_block": _block_permutation(
                    events_part,
                    controls_part,
                    years,
                    iterations=args.permutations,
                    seed=args.seed,
                ),
            },
        }

    # The primary reading is the most conservative level that is still
    # meaningful: year blocks, since slow-planet features are effectively
    # constant within a year.
    significant = [
        family
        for family, body in results.items()
        if body["inference"]["year_block"]["p_value"] < 0.05
    ]

    max_outside = max(
        body["era_balance"]["fraction_outside_event_window"]
        for body in results.values()
    )

    verdict = (
        "association_detected"
        if significant
        else "no_association_detected"
    )

    # Required artifact. The writer refuses a result without it.
    quality = build_control_quality(
        events=events,
        controls_by_family=controls_by_family,
        event_matrix=event_matrix,
        control_matrices=control_matrices,
        layout=layout,
        window=window,
        build_matrix=build_temporal_matrix,
        seed=args.seed,
    )

    written = write_temporal_result(
        {
            "study": "temporal_2a_v2",
            "milestone": "2A_raw_state_event_baselines",
            "verdict": verdict,
            "significant_families_year_block": significant,
            "control_spec_version": CONTROL_SPEC_VERSION,
            "changed_from_v1": (
                "Control specification only. The snapshot, R0 schema, "
                "endpoint, clustering and inclusion rule are identical."
            ),
            "cohort": summarize_catalogue(admitted),
            "window": window.to_dict(),
            "schema": {
                "temporal_schema_hash": temporal_schema_hash(),
                "dimensions": len(layout),
            },
            "clustering": {
                "window_days": CLUSTER_WINDOW_DAYS,
                "radius_km": CLUSTER_RADIUS_KM,
                "clusters": len(set(clusters)),
                "year_blocks": len(set(years)),
            },
            "max_fraction_outside_window": max_outside,
            "control_families": results,
            "location_caveat": (
                "Latitude, longitude and depth are catalogue metadata and "
                "control information. They are not inputs to the geocentric "
                "R0 vector."
            ),
        },
        control_quality=quality,
        output_dir=args.output_dir,
        result_name="earthquake_r0_v2.json",
    )

    print(
        json.dumps(
            {
                "success": True,
                "verdict": verdict,
                "events": len(admitted),
                "max_fraction_outside_window": round(max_outside, 5),
                "families": {
                    family: {
                        "controls": body["controls_after_event_exclusion"],
                        "outside_window": round(
                            body["era_balance"][
                                "fraction_outside_event_window"
                            ],
                            5,
                        ),
                        "mean_year_diff": round(
                            body["era_balance"][
                                "mean_absolute_year_difference"
                            ],
                            2,
                        ),
                        "max_imbalance": round(
                            body["feature_imbalance"][
                                "max_absolute_standardized_difference"
                            ],
                            3,
                        ),
                        "cohens_d": round(body["cohens_d"], 3),
                        "p_event": round(
                            body["inference"]["event_level"]["p_value"], 4
                        ),
                        "p_cluster": round(
                            body["inference"]["cluster_aware"]["p_value"], 4
                        ),
                        "p_year": round(
                            body["inference"]["year_block"]["p_value"], 4
                        ),
                    }
                    for family, body in results.items()
                },
                "control_quality": {
                    "all_families_sound": quality.all_sound,
                    "unsound_families": list(quality.unsound_families),
                    "diagnostic_working": quality.synthetic_control_check[
                        "diagnostic_working"
                    ],
                },
                "artifacts": {k: str(v) for k, v in written.items()},
                "elapsed_seconds": round(perf_counter() - started, 2),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
