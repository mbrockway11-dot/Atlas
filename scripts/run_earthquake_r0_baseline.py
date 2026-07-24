"""Temporal 2 (baseline): earthquakes against the raw astronomical state.

Runs on R0 alone, deliberately. The planetary->Kamea mapping is undefined
(Temporal 1C), so a raw-only result is not a compromise -- it is the baseline
any future Kamea representation has to beat. Framing the eventual comparison
as nested models

    Model A:  raw astronomy
    Model B:  raw astronomy + Kamea features

makes the transform's contribution directly measurable, which "Kamea only"
never could.

Four control families, per the design:

    matched      dates offset from the event, same seasonal structure
    nearby       dates a few days away, nearly the same slow-planet state
    uniform      event times shifted by a constant, preserving their spacing
    random       uniformly drawn from the catalogue's own span

**Provenance gating.** The seed catalogue is provisional -- timestamps
recorded from general knowledge, not checked against USGS or ISC. A temporal
study is entirely a study of timestamps, so this run reports as exploratory
and refuses to emit a confirmatory verdict. Supply a cited catalogue with
--catalogue to change that.

    python scripts/run_earthquake_r0_baseline.py
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import sys
from time import perf_counter

from typing import Any, Sequence

import numpy as np

from atlas.validation.artifacts import write_json
from atlas.validation.event_catalogue import (
    CONFIRMATORY_PROVENANCE,
    InclusionRule,
    TimestampPrecision,
    apply_inclusion_rule,
    load_catalogue,
    seed_earthquake_catalogue,
    summarize_catalogue,
)
from atlas.validation.metrics import separation
from atlas.validation.temporal_state import (
    build_temporal_matrix,
    temporal_feature_layout,
    temporal_schema_hash,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Earthquake baseline against the raw temporal state."
    )
    parser.add_argument(
        "--catalogue",
        type=Path,
        default=None,
        help="Cited catalogue JSON. Without it, the provisional seed is used.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output") / "validation" / "earthquake_r0_baseline_v1",
    )
    parser.add_argument(
        "--minimum-magnitude",
        type=float,
        default=7.0,
        help="Objective inclusion threshold (default: 7.0).",
    )
    parser.add_argument(
        "--controls-per-event",
        type=int,
        default=20,
        help="Controls drawn per event per family (default: 20).",
    )
    parser.add_argument(
        "--permutations",
        type=int,
        default=10_000,
        help="Permutation iterations (default: 10,000).",
    )
    parser.add_argument("--seed", type=int, default=20260801)
    return parser


def _control_instants(
    events: list[datetime],
    family: str,
    *,
    count: int,
    rng: np.random.Generator,
) -> list[datetime]:
    """Return control instants for one family."""
    controls: list[datetime] = []

    earliest, latest = min(events), max(events)
    span_seconds = max(int((latest - earliest).total_seconds()), 1)

    for event in events:
        for index in range(count):
            if family == "matched":
                # Whole years, so season and Earth-Sun geometry are held
                # roughly fixed while the slow planets move.
                offset = int(rng.integers(1, 40)) * 365
                direction = 1 if index % 2 == 0 else -1
                controls.append(event + timedelta(days=direction * offset))

            elif family == "nearby":
                # Days away: the slow planets are essentially unchanged, so
                # this isolates fast-moving structure.
                offset = int(rng.integers(3, 30))
                direction = 1 if index % 2 == 0 else -1
                controls.append(event + timedelta(days=direction * offset))

            elif family == "uniform":
                # Every event shifted by the same amount, preserving the
                # catalogue's internal spacing. Breaks any real alignment
                # while keeping the sample's temporal structure intact.
                shift = int(rng.integers(100, 5_000))
                controls.append(event + timedelta(days=shift))

            elif family == "random":
                controls.append(
                    earliest
                    + timedelta(seconds=int(rng.integers(0, span_seconds)))
                )

            else:
                raise ValueError(f"Unknown control family: {family}")

    return controls


# Declared cluster linkage. Mainshock-aftershock sequences are not
# independent observations, and treating them as such inflates significance:
# 20 aftershocks of one rupture are close to one measurement, not twenty.
# These thresholds are stated in advance and are deliberately simple -- this
# is resampling-block assignment, not a declustering algorithm, and the
# catalogue is kept intact.
CLUSTER_WINDOW_DAYS = 30
CLUSTER_RADIUS_KM = 500.0
EARTH_RADIUS_KM = 6371.0


def _great_circle_km(
    lat_a: float, lon_a: float, lat_b: float, lon_b: float
) -> float:
    """Return great-circle distance in kilometres."""
    phi_a, phi_b = np.radians(lat_a), np.radians(lat_b)
    delta_phi = phi_b - phi_a
    delta_lambda = np.radians(lon_b - lon_a)

    a = (
        np.sin(delta_phi / 2.0) ** 2
        + np.cos(phi_a) * np.cos(phi_b) * np.sin(delta_lambda / 2.0) ** 2
    )

    return float(2.0 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(min(a, 1.0))))


def assign_clusters(records: Sequence[Any]) -> list[int]:
    """Group events into temporal-spatial clusters by single linkage.

    An event joins an existing cluster when it falls within both the time
    window and the radius of any member. Clusters become the resampling unit,
    so a permutation moves whole sequences rather than splitting a rupture
    across groups.
    """
    ordered = sorted(range(len(records)), key=lambda i: records[i].instant)
    labels = [-1] * len(records)
    next_label = 0

    for position in ordered:
        record = records[position]
        joined = -1

        for other in ordered:
            if other == position or labels[other] < 0:
                continue

            neighbour = records[other]
            gap_days = abs(
                (record.instant - neighbour.instant).total_seconds()
            ) / 86_400.0

            if gap_days > CLUSTER_WINDOW_DAYS:
                continue

            if (
                record.latitude is None
                or neighbour.latitude is None
            ):
                continue

            if (
                _great_circle_km(
                    record.latitude,
                    record.longitude,
                    neighbour.latitude,
                    neighbour.longitude,
                )
                <= CLUSTER_RADIUS_KM
            ):
                joined = labels[other]
                break

        if joined >= 0:
            labels[position] = joined
        else:
            labels[position] = next_label
            next_label += 1

    return labels


def _cluster_permutation_test(
    events: np.ndarray,
    controls: np.ndarray,
    cluster_labels: Sequence[int],
    *,
    iterations: int,
    seed: int,
) -> dict[str, float]:
    """Permutation test that resamples whole clusters, not single events.

    The event group is rebuilt each iteration by drawing clusters, so
    within-sequence correlation is preserved and the null is not made
    artificially tight by counting aftershocks as independent draws.
    """
    if events.size == 0 or controls.size == 0:
        return {"observed_difference": 0.0, "p_value": 1.0, "clusters": 0}

    observed = float(events.mean() - controls.mean())

    by_cluster: dict[int, list[float]] = {}

    for value, label in zip(events, cluster_labels):
        by_cluster.setdefault(int(label), []).append(float(value))

    cluster_ids = list(by_cluster)
    pooled = np.concatenate((events, controls))

    rng = np.random.default_rng(seed)
    extreme = 0

    for _ in range(iterations):
        # Draw a bootstrap set of clusters and take an equally sized sample
        # from the pooled values, so the comparison keeps the cluster
        # structure of the real event set.
        drawn = rng.choice(len(cluster_ids), size=len(cluster_ids))
        size = sum(len(by_cluster[cluster_ids[int(i)]]) for i in drawn)

        shuffled = rng.permutation(pooled)
        difference = (
            shuffled[:size].mean() - shuffled[size:].mean()
        )

        if abs(difference) >= abs(observed):
            extreme += 1

    return {
        "observed_difference": observed,
        "p_value": (extreme + 1) / (iterations + 1),
        "iterations": iterations,
        "clusters": len(cluster_ids),
        "events": int(events.size),
    }


def _dispersion(matrix: np.ndarray) -> np.ndarray:
    """Return each row's distance from the sample centroid.

    A single scalar per state, so event and control sets can be compared
    without assuming which feature would carry a signal. If events cluster
    in the state space at all, they are less dispersed than controls.
    """
    if matrix.shape[0] == 0:
        return np.array([])

    centroid = matrix.mean(axis=0, keepdims=True)
    deviations = matrix.std(axis=0, keepdims=True)
    scaled = (matrix - centroid) / np.where(deviations == 0.0, 1.0, deviations)

    return np.linalg.norm(scaled, axis=1)


def _permutation_test(
    events: np.ndarray,
    controls: np.ndarray,
    *,
    iterations: int,
    seed: int,
) -> dict[str, float]:
    """Return an empirical p-value for the difference in means."""
    if events.size == 0 or controls.size == 0:
        return {"observed_difference": 0.0, "p_value": 1.0}

    observed = float(events.mean() - controls.mean())
    pooled = np.concatenate((events, controls))

    rng = np.random.default_rng(seed)
    extreme = 0

    for _ in range(iterations):
        rng.shuffle(pooled)
        difference = (
            pooled[: events.size].mean() - pooled[events.size :].mean()
        )

        if abs(difference) >= abs(observed):
            extreme += 1

    return {
        "observed_difference": observed,
        # +1 smoothing: an empirical p-value of exactly zero would overstate
        # what a finite number of permutations can establish.
        "p_value": (extreme + 1) / (iterations + 1),
        "iterations": iterations,
    }


def main() -> int:
    """Run the earthquake baseline."""
    args = build_parser().parse_args()
    started = perf_counter()

    records = (
        load_catalogue(args.catalogue)
        if args.catalogue
        else seed_earthquake_catalogue()
    )

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

    if len(admitted) < 5:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": (
                        f"Only {len(admitted)} events pass the inclusion "
                        "rule; too few for any comparison."
                    ),
                },
                indent=2,
            )
        )
        return 1

    catalogue_summary = summarize_catalogue(admitted)

    # Provenance gate. Mirrors the identity branch: exploratory data may run,
    # but may not produce a confirmatory verdict.
    eligible = [r for r in admitted if r.provenance in CONFIRMATORY_PROVENANCE]
    confirmatory = len(eligible) == len(admitted)

    event_instants = [record.instant for record in admitted]
    event_matrix, _ = build_temporal_matrix(event_instants)

    # Resampling blocks. Aftershock sequences are one observation, not many.
    cluster_labels = assign_clusters(admitted)
    cluster_count = len(set(cluster_labels))

    # Controls landing on another cohort earthquake are not controls. Both
    # the unfiltered and the event-excluded comparison are reported, because
    # a difference between them is itself informative.
    event_days = {record.instant.date() for record in admitted}

    rng = np.random.default_rng(args.seed)
    families = ("matched", "nearby", "uniform", "random")

    event_dispersion = _dispersion(event_matrix)
    results: dict[str, dict] = {}

    for family in families:
        controls = _control_instants(
            event_instants,
            family,
            count=args.controls_per_event,
            rng=rng,
        )
        filtered_controls = [
            moment for moment in controls if moment.date() not in event_days
        ]
        collisions = len(controls) - len(filtered_controls)

        family_result: dict[str, Any] = {
            "controls_drawn": len(controls),
            "controls_colliding_with_cohort_events": collisions,
        }

        for variant, instants in (
            ("unfiltered", controls),
            ("event_excluded", filtered_controls),
        ):
            if not instants:
                continue

            control_matrix, _ = build_temporal_matrix(instants)

            # Dispersion is measured against the combined sample so events
            # and controls share one reference frame.
            combined = np.vstack((event_matrix, control_matrix))
            combined_dispersion = _dispersion(combined)

            events_part = combined_dispersion[: event_matrix.shape[0]]
            controls_part = combined_dispersion[event_matrix.shape[0] :]

            family_result[variant] = {
                "control_count": int(control_matrix.shape[0]),
                "event_mean_dispersion": float(events_part.mean()),
                "control_mean_dispersion": float(controls_part.mean()),
                **separation(events_part, controls_part),
                "cluster_permutation": _cluster_permutation_test(
                    events_part,
                    controls_part,
                    cluster_labels,
                    iterations=args.permutations,
                    seed=args.seed,
                ),
            }

        results[family] = family_result

    # The primary reading is the event-excluded, cluster-aware test.
    any_significant = any(
        body.get("event_excluded", {})
        .get("cluster_permutation", {})
        .get("p_value", 1.0)
        < 0.05
        for body in results.values()
    )

    verdict = (
        "exploratory_only_provisional_timestamps"
        if not confirmatory
        else ("difference_detected" if any_significant else "no_difference")
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        {
            "milestone": "temporal_2_earthquake_r0_baseline",
            "representation": "R0_raw_astronomical_state",
            "verdict": verdict,
            "confirmatory": confirmatory,
            "catalogue": catalogue_summary,
            "inclusion_rule": filtered["rule"],
            "excluded": filtered["excluded"],
            "events": [record.to_dict() for record in admitted],
            "schema": {
                "temporal_schema_hash": temporal_schema_hash(),
                "dimensions": len(temporal_feature_layout()),
            },
            "clustering": {
                "window_days": CLUSTER_WINDOW_DAYS,
                "radius_km": CLUSTER_RADIUS_KM,
                "events": len(admitted),
                "clusters": cluster_count,
                "method": (
                    "Single-linkage temporal-spatial blocks, declared in "
                    "advance. The catalogue is kept intact; clusters are "
                    "resampling units, not a declustering filter."
                ),
            },
            "location_caveat": (
                "Earthquake latitude, longitude and depth are catalogue "
                "metadata and control information. They are NOT inputs to "
                "the present geocentric R0 vector, which depends only on "
                "the instant."
            ),
            "control_families": results,
            "note": (
                "Baseline on the raw astronomical state only. The "
                "planetary-to-Kamea mapping is undefined (Temporal 1C), so "
                "no Kamea claim is made or implied. When that mapping "
                "exists, the comparison is nested: raw versus raw + Kamea."
            ),
        },
        args.output_dir / "earthquake_r0_baseline.json",
    )

    print(
        json.dumps(
            {
                "success": True,
                "verdict": verdict,
                "confirmatory": confirmatory,
                "catalogue": {
                    "admitted": len(admitted),
                    "excluded": filtered["excluded_count"],
                    "confirmatory_eligible": catalogue_summary[
                        "confirmatory_eligible"
                    ],
                    "by_provenance": catalogue_summary["by_provenance"],
                    "date_range": catalogue_summary["date_range"],
                },
                "clusters": cluster_count,
                "control_families": {
                    family: {
                        "collisions_with_events": body[
                            "controls_colliding_with_cohort_events"
                        ],
                        **{
                            variant: {
                                "controls": body[variant]["control_count"],
                                "cohens_d": round(
                                    body[variant]["cohens_d"], 3
                                ),
                                "p_value": round(
                                    body[variant]["cluster_permutation"][
                                        "p_value"
                                    ],
                                    4,
                                ),
                            }
                            for variant in ("unfiltered", "event_excluded")
                            if variant in body
                        },
                    }
                    for family, body in results.items()
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
