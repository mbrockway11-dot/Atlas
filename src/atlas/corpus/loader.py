"""Corpus loaders."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_corpus_csv(path: str | Path = "research/corpus/vectors.csv") -> pd.DataFrame:
    """Load corpus vectors CSV."""
    return pd.read_csv(path)