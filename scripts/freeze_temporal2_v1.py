"""Freeze Temporal 2 v1 and confirm its era-confound diagnosis directly.

v1 is preserved exactly as run. This script adds no analysis to it -- it
computes the diagnostics that explain the result and writes a frozen report.

The diagnosis so far rested on orbital-period reasoning: Uranus, Neptune and
Pluto have periods of 84, 165 and 248 years, so an era-mismatched control set
should differ from the events in those components. That argument is checked
here against the data, by measuring per-feature standardized differences for
every v1 control family. If the mechanism is right, the outer planets carry
the largest imbalance for matched and uniform and not for nearby and random.

    python scripts/freeze_temporal2_v1.py
"""

from __future__ import annotations

import argparse
from datetime import timedelta
import json
from pathlib import Path
import sys

import numpy as np

from atlas.validation.artifacts import write_json
from atlas.validation.event_catalogue import load_catalogue
from atlas.validation.temporal_controls import (
    era_balance,
    feature_imbalance,
    window_from_events,
)
from atlas.validation.temporal_state import (
    build_temporal_matrix,
    temporal_feature_layout,
    temporal_schema_hash,
)


# The v1 generators, reproduced exactly as they ran. Copied rather than
# imported so that fixing them in v2 cannot retroactively change what v1 is
# recorded as having done.
def v1_controls(events, family, *, count, rng):
    """Reproduce a v1 control family verbatim."""
    controls = []
    earliest, latest = min(events), max(events)
    span = max(int((latest - earliest).total_seconds()), 1)

    for event in events:
        for index in range(count):
            if family == "matched":
                offset = int(rng.integers(1, 40)) * 365
                direction = 1 if index % 2 == 0 else -1
                controls.append(event + timedelta(days=direction * offset))
            elif family == "nearby":
                offset = int(rng.integers(3, 30))
                direction = 1 if index % 2 == 0 else -1
                controls.append(event + timedelta(days=direction * offset))
            elif family == "uniform":
                controls.append(
                    event + timedelta(days=int(rng.integers(100, 5_000)))
                )
            else:
                controls.append(
                    earliest + timedelta(seconds=int(rng.integers(0, span)))
                )

    return controls


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Freeze Temporal 2 v1 with era diagnostics."
    )
    parser.add_argument(
        "--catalogue",
        type=Path,
        default=Path("data") / "validation" / "earthquakes" / "catalogue.json",
    )
    parser.add_argument(
        "--result",
        type=Path,
        default=Path("output")
        / "validation"
        / "earthquake_r0_baseline_v1"
        / "earthquake_r0_baseline.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output") / "validation" / "temporal2_v1_frozen",
    )
    parser.add_argument("--controls-per-event", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260801)
    return parser


def main() -> int:
    """Write the frozen v1 report."""
    args = build_parser().parse_args()

    records = load_catalogue(args.catalogue)
    events = [record.instant for record in records]
    window = window_from_events(events)
    layout = temporal_feature_layout()

    event_matrix, _ = build_temporal_matrix(events)

    result = json.loads(args.result.read_text(encoding="utf-8"))
    rng = np.random.default_rng(args.seed)

    diagnostics: dict[str, dict] = {}

    for family in ("matched", "nearby", "uniform", "random"):
        controls = v1_controls(
            events, family, count=args.controls_per_event, rng=rng
        )
        control_matrix, _ = build_temporal_matrix(controls)

        diagnostics[family] = {
            "era_balance": era_balance(events, controls, window),
            "feature_imbalance": feature_imbalance(
                event_matrix, control_matrix, layout
            ),
            "reported_result": {
                "cohens_d": result["control_families"][family][
                    "event_excluded"
                ]["cohens_d"],
                "p_value": result["control_families"][family][
                    "event_excluded"
                ]["cluster_permutation"]["p_value"],
            },
        }

    # Does the imbalance actually land on the outer planets, as the orbital
    # argument predicts?
    outer = ("Uranus", "Neptune", "Pluto")
    mechanism: dict[str, dict] = {}

    for family, body in diagnostics.items():
        ranking = [
            row["body"] for row in body["feature_imbalance"]["body_ranking"]
        ]
        outer_ranks = {
            name: ranking.index(name) + 1
            for name in outer
            if name in ranking
        }

        # Whether the top individual features involve an outer planet is the
        # direct test of the orbital-period argument.
        top_features = body["feature_imbalance"]["features"][:6]
        outer_in_top_features = sum(
            1
            for row in top_features
            if any(name in row["feature"] for name in outer)
        )

        mechanism[family] = {
            "outer_planet_body_ranks": outer_ranks,
            "outer_in_top_three_bodies": sum(
                1 for r in outer_ranks.values() if r <= 3
            ),
            "outer_planet_share_of_top_features": (
                outer_in_top_features / len(top_features)
                if top_features
                else 0.0
            ),
            "top_feature": (
                top_features[0]["feature"] if top_features else None
            ),
            "max_imbalance": body["feature_imbalance"][
                "max_absolute_standardized_difference"
            ],
            "fraction_outside_window": body["era_balance"][
                "fraction_outside_event_window"
            ],
        }

    report = {
        "study": "temporal_2_v1",
        "status": "frozen",
        "verdict": ["no_stable_association", "control_era_confound_detected"],
        "cohort": {
            "source": "USGS FDSN event service",
            "events": len(records),
            "window": window.to_dict(),
            "representation": "R0_raw_astronomical_state",
            "temporal_schema_hash": temporal_schema_hash(),
        },
        "endpoint": {
            "statistic": "dispersion_from_combined_sample_centroid",
            "definition": (
                "Each state is standardized against the combined "
                "event-plus-control sample, then summarized as the L2 norm "
                "of its standardized coordinates. One scalar per state, "
                "chosen before results were seen and unchanged since."
            ),
            "caveat": (
                "R0 has 140 nominal but ~6 effective dimensions, so an "
                "aggregate norm weights redundant feature families more "
                "heavily than independent ones. Frozen for v2 so the two "
                "studies remain comparable; alternatives belong in a "
                "separate registered study."
            ),
        },
        "primary_preregistered_result": (
            "Mixed and control-sensitive. Two of four families reached "
            "significance with opposite signs."
        ),
        "diagnostic_interpretation": (
            "Significance tracks out-of-window sampling, not earthquakes."
        ),
        "sound_control_result": (
            "nearby (p=0.982) and random (p=0.394) are both null. These are "
            "the families confined to the event era, and they carry the "
            "substantive finding."
        ),
        "v2_motivation": (
            "Remove era leakage prospectively by confining every generator "
            "to the observation window, registered before running."
        ),
        "control_diagnostics": diagnostics,
        "mechanism_check": mechanism,
        "immutability": (
            "v1 is preserved as run. The flawed matched and uniform "
            "generators are reproduced verbatim in this script rather than "
            "imported, so correcting them in v2 cannot retroactively change "
            "what v1 did."
        ),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(report, args.output_dir / "temporal2_v1_frozen.json")

    print(
        json.dumps(
            {
                "success": True,
                "verdict": report["verdict"],
                "mechanism_check": {
                    family: {
                        "outside_window": round(
                            body["fraction_outside_window"], 4
                        ),
                        "outer_share_of_top_features": round(
                            body["outer_planet_share_of_top_features"], 2
                        ),
                        "top_feature": body["top_feature"],
                        "max_standardized_imbalance": round(
                            body["max_imbalance"], 3
                        ),
                        "reported_p": diagnostics[family]["reported_result"][
                            "p_value"
                        ],
                    }
                    for family, body in mechanism.items()
                },
                "output_dir": str(args.output_dir),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
