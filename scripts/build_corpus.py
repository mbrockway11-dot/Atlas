"""Build Atlas research corpus."""

from atlas.corpus import build_research_corpus


if __name__ == "__main__":
    result = build_research_corpus(
        profile_library="output/library/profiles",
        output_directory="research/corpus",
        normalization_mode="percentile",
    )

    print(f"Built corpus with {result['profile_count']} profiles.")
    print(f"CSV: {result['exports']['csv']}")
    print(f"Parquet: {result['exports']['parquet']}")
    print(f"Metadata: {result['exports']['metadata']}")