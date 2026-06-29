"""Compare two Atlas corpus profiles."""

from __future__ import annotations

import argparse

from atlas.comparison import compare_profiles
from atlas.corpus.loader import load_corpus_csv


def main() -> None:
    """Run profile comparison CLI."""
    parser = argparse.ArgumentParser(
        description="Compare two profiles in the Atlas corpus."
    )

    parser.add_argument("profile_a", help="First profile name.")
    parser.add_argument("profile_b", help="Second profile name.")

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
        "--min-std",
        type=float,
        default=0.005,
        help="Minimum feature standard deviation to include.",
    )

    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of feature differences to show.",
    )

    args = parser.parse_args()

    dataframe = load_corpus_csv(args.corpus)

    comparison = compare_profiles(
        dataframe=dataframe,
        profile_a=args.profile_a,
        profile_b=args.profile_b,
        metric=args.metric,
        min_std=args.min_std,
        top_n=args.top,
    )

    print("")
    print("=" * 72)
    print("Atlas Identity Comparison")
    print("=" * 72)
    print(f"Profile A      : {comparison.profile_a}")
    print(f"Profile B      : {comparison.profile_b}")
    print(f"Metric         : {comparison.metric}")
    print(f"Similarity     : {comparison.similarity:.4f}")
    print(f"Distance       : {comparison.distance:.4f}")
    print(f"Feature Count  : {comparison.feature_count}")

    print("")
    print("Interpretation")
    print("-" * 72)
    for line in comparison.interpretation_lines:
        print(f"- {line}")

    print("")
    print("Planet Difference Summary")
    print("-" * 72)
    for row in comparison.planet_summary["ranked_planets"]:
        print(
            f"{row['planet']:<10} "
            f"mean_delta={row['mean_difference']:.4f} "
            f"level={row['difference_level']}"
        )

    print("")
    print("Most Similar Features")
    print("-" * 72)
    for row in comparison.most_similar_features:
        print(
            f"{row['feature']:<45} "
            f"delta_z={row['standardized_difference']:.4f} "
            f"a={row['value_a']:.4f} "
            f"b={row['value_b']:.4f}"
        )

    print("")
    print("Most Different Features")
    print("-" * 72)
    for row in comparison.most_different_features:
        print(
            f"{row['feature']:<45} "
            f"delta_z={row['standardized_difference']:.4f} "
            f"a={row['value_a']:.4f} "
            f"b={row['value_b']:.4f}"
        )


if __name__ == "__main__":
    main()