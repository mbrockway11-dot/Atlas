"""Atlas corpus similarity search."""

from __future__ import annotations

import argparse

from atlas.corpus.search import CorpusSearch


def main() -> None:
    """Run corpus similarity search."""
    parser = argparse.ArgumentParser(
        description="Search Atlas Research Corpus."
    )

    parser.add_argument(
        "name",
        help="Profile name",
    )

    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of nearest profiles.",
    )

    parser.add_argument(
        "--corpus",
        default="research/corpus/vectors.csv",
        help="Corpus CSV.",
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
        "--show-features",
        action="store_true",
        help="Show feature-level explanation for the top match.",
    )

    parser.add_argument(
        "--feature-count",
        type=int,
        default=8,
        help="Number of similar/different features to show.",
    )

    args = parser.parse_args()

    corpus = CorpusSearch(args.corpus)

    if not corpus.contains(args.name):
        print("")
        print(f'Profile "{args.name}" not found.')
        print("")
        print("Available profiles:")
        for profile in corpus.profile_names():
            print(f"  - {profile}")
        return

    results = corpus.search(
        profile_name=args.name,
        top_n=args.top,
        metric=args.metric,
        min_std=args.min_std,
    )

    print("")
    print("=" * 70)
    print("Atlas Corpus Search")
    print("=" * 70)
    print(f"Reference Profile : {args.name}")
    print(f"Corpus Size       : {corpus.profile_count}")
    print(f"Metric            : {args.metric}")
    print(f"Min Std           : {args.min_std}")
    print("")

    records = results.to_dict("records")

    for index, row in enumerate(records, start=1):
        print(
            f"{index:>2}. "
            f"{row['name']:<40} "
            f"similarity={row['similarity']:.4f} "
            f"distance={row['distance']:.4f}"
        )

    if args.show_features and records:
        top_match = records[0]["name"]
        explanation = corpus.explain_match(
            profile_a=args.name,
            profile_b=top_match,
            min_std=args.min_std,
            top_n=args.feature_count,
        )

        print("")
        print("=" * 70)
        print(f"Feature Explanation: {args.name} ↔ {top_match}")
        print("=" * 70)

        print("")
        print("Most similar standardized features:")
        for row in explanation["most_similar_features"]:
            print(
                f"  {row['feature']:<45} "
                f"Δz={row['standardized_difference']:.4f} "
                f"raw_a={row['value_a']:.4f} "
                f"raw_b={row['value_b']:.4f}"
            )

        print("")
        print("Most different standardized features:")
        for row in explanation["most_different_features"]:
            print(
                f"  {row['feature']:<45} "
                f"Δz={row['standardized_difference']:.4f} "
                f"raw_a={row['value_a']:.4f} "
                f"raw_b={row['value_b']:.4f}"
            )


if __name__ == "__main__":
    main()