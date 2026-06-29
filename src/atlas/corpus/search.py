"""Corpus search utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from atlas.corpus.loader import load_corpus_csv
from atlas.corpus.similarity import (
    SimilarityMetric,
    explain_profile_difference,
    find_nearest_profiles,
)


class CorpusSearch:
    """Search interface for Atlas research corpus."""

    def __init__(
        self,
        corpus_path: str | Path = "research/corpus/vectors.csv",
    ):
        self.corpus_path = Path(corpus_path)
        self.dataframe = load_corpus_csv(self.corpus_path)

    @property
    def profile_count(self) -> int:
        """Number of profiles in the corpus."""
        return len(self.dataframe)

    def search(
        self,
        profile_name: str,
        top_n: int = 10,
        metric: SimilarityMetric = "euclidean",
        min_std: float = 0.005,
    ) -> pd.DataFrame:
        """Find structurally similar profiles."""
        return find_nearest_profiles(
            dataframe=self.dataframe,
            profile_name=profile_name,
            top_n=top_n,
            metric=metric,
            min_std=min_std,
        )

    def explain_match(
        self,
        profile_a: str,
        profile_b: str,
        min_std: float = 0.005,
        top_n: int = 10,
    ) -> dict[str, Any]:
        """Explain why two profiles are similar or different."""
        return explain_profile_difference(
            dataframe=self.dataframe,
            profile_a=profile_a,
            profile_b=profile_b,
            min_std=min_std,
            top_n=top_n,
        )

    def profile_names(self) -> list[str]:
        """Return sorted profile names."""
        return sorted(self.dataframe["name"].tolist())

    def contains(self, profile_name: str) -> bool:
        """Check whether a profile exists."""
        return profile_name in self.dataframe["name"].values