"""Run Atlas corpus feature diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from atlas.corpus.diagnostics import (
    build_feature_diagnostics_from_csv,
    diagnostics_to_dict,
)


def main() -> None:
    """Run corpus diagnostics from CLI."""
    parser = argparse.ArgumentParser(
        description="Diagnose Atlas corpus feature variance and redundancy."
    )

    parser.add_argument(
        "--path",
        default="research/corpus/vectors.csv",
        help="Path to corpus vectors CSV.",
    )

    parser.add_argument(
        "--output",
        default="research/corpus/feature_diagnostics.json",
        help="Output diagnostics JSON path.",
    )

    args = parser.parse_args()

    diagnostics = build_feature_diagnostics_from_csv(args.path)
    data = diagnostics_to_dict(diagnostics)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )

    print("")
    print("Atlas Corpus Feature Diagnostics")
    print("=" * 56)
    print(f"Profiles: {diagnostics.profile_count}")
    print(f"Features: {diagnostics.feature_count}")
    print(f"Near-constant features: {diagnostics.summary['near_constant_count']}")
    print(
        "Highly correlated pairs: "
        f"{diagnostics.summary['highly_correlated_pair_count']}"
    )
    print(f"Mean feature std: {diagnostics.summary['mean_feature_std']:.6f}")
    print(f"Median feature std: {diagnostics.summary['median_feature_std']:.6f}")
    print("")

    print("Highest variance features:")
    for row in diagnostics.highest_variance_features[:10]:
        print(
            f"  {row['feature']:<45} "
            f"std={row['std']:.6f} var={row['variance']:.6f}"
        )

    print("")
    print("Lowest variance features:")
    for row in diagnostics.lowest_variance_features[:10]:
        print(
            f"  {row['feature']:<45} "
            f"std={row['std']:.6f} var={row['variance']:.6f}"
        )

    print("")
    print(f"Wrote diagnostics: {output_path}")


if __name__ == "__main__":
    main()