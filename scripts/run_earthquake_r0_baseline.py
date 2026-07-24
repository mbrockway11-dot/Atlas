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
        control_matrix, _ = build_temporal_matrix(controls)

        # Dispersion is measured against the combined sample so events and
        # controls share one reference frame.
        combined = np.vstack((event_matrix, control_matrix))
        combined_dispersion = _dispersion(combined)

        events_part = combined_dispersion[: event_matrix.shape[0]]
        controls_part = combined_dispersion[event_matrix.shape[0] :]

        results[family] = {
            "control_count": int(control_matrix.shape[0]),
            "event_mean_dispersion": float(events_part.mean()),
            "control_mean_dispersion": float(controls_part.mean()),
            **separation(events_part, controls_part),
            "permutation": _permutation_test(
                events_part,
                controls_part,
                iterations=args.permutations,
                seed=args.seed,
            ),
        }

    any_significant = any(
        body["permutation"]["p_value"] < 0.05 for body in results.values()
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
                "control_families": {
                    family: {
                        "controls": body["control_count"],
                        "event_dispersion": round(
                            body["event_mean_dispersion"], 4
                        ),
                        "control_dispersion": round(
                            body["control_mean_dispersion"], 4
                        ),
                        "cohens_d": round(body["cohens_d"], 3),
                        "p_value": round(body["permutation"]["p_value"], 4),
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
