"""Run Atlas ablation experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from atlas.ablation.experiments import (
    all_default_experiments,
)
from atlas.ablation.harness import (
    ablation_result_to_dict,
    run_ablation_experiment,
)
from atlas.ablation.reports import render_ablation_report_text
from atlas.corpus.loader import load_corpus_csv


def main() -> None:
    """Run default ablation experiments."""
    parser = argparse.ArgumentParser(
        description="Run Atlas corpus ablation experiments."
    )

    parser.add_argument(
        "reference_profile",
        help="Profile name to use as ablation reference.",
    )

    parser.add_argument(
        "--corpus",
        default="research/corpus/vectors.csv",
        help="Corpus CSV path.",
    )

    parser.add_argument(
        "--metric",
        default="euclidean",
        choices=[
            "euclidean",
            "manhattan",
            "pearson",
            "cosine",
        ],
        help="Similarity metric.",
    )

    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Nearest-neighbor list size.",
    )

    parser.add_argument(
        "--output",
        default="research/corpus/ablation_report.json",
        help="Output JSON report path.",
    )

    args = parser.parse_args()

    dataframe = load_corpus_csv(args.corpus)
    experiments = all_default_experiments()

    results = [
        run_ablation_experiment(
            dataframe=dataframe,
            reference_profile=args.reference_profile,
            experiment=experiment,
            metric=args.metric,
            top_n=args.top,
        )
        for experiment in experiments
    ]

    data = {
        "reference_profile": args.reference_profile,
        "metric": args.metric,
        "results": [
            ablation_result_to_dict(result)
            for result in results
        ],
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )

    print("")
    print(render_ablation_report_text(results))
    print("")
    print(f"Wrote ablation report: {output_path}")


if __name__ == "__main__":
    main()