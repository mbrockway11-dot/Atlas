"""Cluster Atlas corpus profiles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from atlas.corpus.loader import load_corpus_csv
from atlas.features.clustering import (
    cluster_corpus,
    cluster_result_to_dict,
)


def main() -> None:
    """Run corpus clustering."""
    parser = argparse.ArgumentParser(
        description="Cluster Atlas corpus profiles."
    )

    parser.add_argument(
        "--corpus",
        default="research/corpus/vectors.csv",
        help="Corpus CSV path.",
    )

    parser.add_argument(
        "--clusters",
        type=int,
        default=4,
        help="Number of clusters.",
    )

    parser.add_argument(
        "--min-std",
        type=float,
        default=0.005,
        help="Minimum feature standard deviation.",
    )

    parser.add_argument(
        "--output",
        default="research/corpus/clusters.json",
        help="Output JSON path.",
    )

    args = parser.parse_args()

    dataframe = load_corpus_csv(args.corpus)

    result = cluster_corpus(
        dataframe=dataframe,
        cluster_count=args.clusters,
        min_std=args.min_std,
    )

    data = cluster_result_to_dict(result)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )

    print("")
    print("Atlas Corpus Clustering")
    print("=" * 56)
    print(f"Profiles: {len(dataframe)}")
    print(f"Clusters: {result.cluster_count}")
    print(f"Features: {result.feature_count}")
    print("")

    for cluster in result.clusters:
        print(
            f"Cluster {cluster['cluster_id']}: "
            f"size={cluster['size']} "
            f"representative={cluster['representative']} "
            f"mean_distance={cluster['mean_distance_to_centroid']:.4f}"
        )

        print("  Members:")
        for member in cluster["members"]:
            print(f"    - {member}")

        print("  Dominant features:")
        for feature in cluster["dominant_features"][:5]:
            print(
                f"    - {feature['feature']}: "
                f"{feature['centroid_value']:.4f}"
            )

        print("")

    print("Top outliers:")
    for row in result.outliers[:10]:
        print(
            f"  - {row['name']}: "
            f"cluster={row['cluster_id']} "
            f"distance={row['distance_to_centroid']:.4f}"
        )

    print("")
    print(f"Wrote clusters: {output_path}")


if __name__ == "__main__":
    main()