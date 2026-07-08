
"""Load Sigil V32 live outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


DEFAULT_SIGIL_ROOT = Path(r"C:\Projects\sigil-engine-git")


def output_path(root: str | Path, name: str) -> Path:
    return Path(root) / "output" / name


def load_csv(root: str | Path, name: str) -> pd.DataFrame:
    path = output_path(root, name)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_engine_states(root: str | Path = DEFAULT_SIGIL_ROOT) -> pd.DataFrame:
    return load_csv(root, "v32_ab_live_engine_states.csv")


def load_combined_decision(root: str | Path = DEFAULT_SIGIL_ROOT) -> pd.DataFrame:
    return load_csv(root, "v32_ab_live_combined_decision.csv")


def load_signal_snapshot(root: str | Path = DEFAULT_SIGIL_ROOT) -> pd.DataFrame:
    return load_csv(root, "v32_ab_live_signal_snapshot.csv")
