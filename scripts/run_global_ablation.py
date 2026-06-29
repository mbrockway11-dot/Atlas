"""Run corpus-wide Atlas ablation experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from atlas.ablation.global_harness import (
    global_ablation_result_to_dict,
    run_default_global_ablation,
)
from atlas.ablation.reports import render_global_ablation_report_text
from atlas.corpus.loader import load_corpus_csv


def main() -> None:
    """Run global ablation experiments."""
    parser = argparse.ArgumentParser(
        description="Run Atlas global corpus ablation experiments."
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
        default="research/corpus/global_ablation_report.json",
        help="Output JSON report path.",
    )

    args = parser.parse_args()

    dataframe = load_corpus_csv(args.corpus)

    results = run_default_global_ablation(
        dataframe=dataframe,
        metric=args.metric,
        top_n=args.top,
    )

    data = {
        "metric": args.metric,
        "profile_count": int(len(dataframe)),
        "results": [
            global_ablation_result_to_dict(result)
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
    print(render_global_ablation_report_text(results))
    print("")
    print(f"Wrote global ablation report: {output_path}")


if __name__ == "__main__":
    main()