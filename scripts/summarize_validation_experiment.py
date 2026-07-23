"""Summarize a completed validation experiment.

    python scripts/summarize_validation_experiment.py \
        output/validation/identity_random_pair_baseline_v1

Reads only the small JSON artifacts, so it stays fast regardless of how many
pairs the run produced. Pass --score to place a value in the population
distribution -- the deterministic score and its percentile are reported as
separate quantities, because a high score means nothing until it is located
against the population.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from atlas.validation.statistics import DistributionSummary, percentile_of


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Summarize a completed Atlas validation experiment."
    )
    parser.add_argument(
        "experiment_dir",
        type=Path,
        help="Experiment output directory.",
    )
    parser.add_argument(
        "--score",
        type=float,
        default=None,
        metavar="VALUE",
        help="Report the population percentile of this score.",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print the full Markdown report instead of the JSON summary.",
    )
    return parser


def _load(path: Path) -> dict:
    """Load a JSON artifact, or an empty mapping when absent."""
    if not path.is_file():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def main() -> int:
    """Print a summary of one experiment."""
    args = build_parser().parse_args()
    directory = args.experiment_dir

    if not directory.is_dir():
        print(
            json.dumps(
                {"success": False, "error": f"No such directory: {directory}"},
                indent=2,
            )
        )
        return 1

    if args.report:
        report_path = directory / "report.md"

        if not report_path.is_file():
            print(f"No report at {report_path}", file=sys.stderr)
            return 1

        print(report_path.read_text(encoding="utf-8"))
        return 0

    experiment = _load(directory / "experiment.json")
    provenance = _load(directory / "provenance.json")
    distribution = _load(directory / "distribution.json")
    strata = _load(directory / "strata.json")

    summary: dict[str, object] = {
        "success": bool(distribution),
        "experiment_id": experiment.get("experiment_id"),
        "domain": experiment.get("domain"),
        "kind": experiment.get("kind"),
        "corpus": provenance.get("corpus", {}),
        "build": provenance.get("build", {}),
        "distribution": {
            key: distribution.get(key)
            for key in (
                "count",
                "mean",
                "median",
                "stddev",
                "minimum",
                "maximum",
                "skewness",
                "kurtosis",
                "distinct_scores",
                "duplicate_score_fraction",
                "exact_collision_pairs",
            )
        },
        "confounders": strata.get("confounders", []),
    }

    if args.score is not None and distribution.get("histogram"):
        histogram = distribution["histogram"]

        reconstructed = DistributionSummary(
            count=int(distribution["count"]),
            mean=float(distribution["mean"]),
            median=float(distribution["median"]),
            stddev=float(distribution["stddev"]),
            variance=float(distribution["variance"]),
            minimum=float(distribution["minimum"]),
            maximum=float(distribution["maximum"]),
            skewness=float(distribution["skewness"]),
            kurtosis=float(distribution["kurtosis"]),
            percentiles=dict(distribution["percentiles"]),
            histogram_counts=tuple(histogram["counts"]),
            histogram_edges=tuple(histogram["edges"]),
            distinct_scores=int(distribution["distinct_scores"]),
            duplicate_score_fraction=float(
                distribution["duplicate_score_fraction"]
            ),
        )

        summary["query"] = {
            "score": args.score,
            "population_percentile": round(
                percentile_of(reconstructed, args.score), 4
            ),
            "note": (
                "The deterministic score and its population percentile are "
                "separate quantities. A percentile is not evidence of a "
                "relationship; it locates the score against unrelated pairs."
            ),
        }

    print(json.dumps(summary, indent=2, default=str))

    return 0


if __name__ == "__main__":
    sys.exit(main())
