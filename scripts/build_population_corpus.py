"""Build Atlas population corpus archive."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from atlas.population import (
    build_population_corpus,
    population_index_to_json,
)
from atlas.services.profile_service import list_profile_keys


DEFAULT_OUTPUT_DIR = Path("output/corpus")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--evaluation-date", default="2026-07-02")
    parser.add_argument("--forecast-days", type=int, default=3)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    profile_keys = list_profile_keys()

    if args.limit is not None:
        profile_keys = profile_keys[: args.limit]

    print(f"Building population corpus for {len(profile_keys)} profile(s)...")

    result = build_population_corpus(
        profile_keys,
        evaluation_date=args.evaluation_date,
        forecast_days=args.forecast_days,
    )

    index_json = population_index_to_json(result.index)

    (output_dir / "population_index.json").write_text(
        index_json,
        encoding="utf-8",
    )

    summary = result.to_dict()
    summary.pop("index", None)

    (output_dir / "corpus_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    failures = {
        "failure_count": result.failure_count,
        "failures": result.failures,
    }

    (output_dir / "corpus_failures.json").write_text(
        json.dumps(failures, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    warnings = {
        "warning_profile_count": len(result.warnings),
        "warnings": result.warnings,
    }

    (output_dir / "corpus_warnings.json").write_text(
        json.dumps(warnings, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print("Done.")
    print(result.to_dict()["summary"])
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    main()
