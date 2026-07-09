
"""Shared safe IO helpers for Atlas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def safe_read_csv(path: str | Path) -> pd.DataFrame:
    p = Path(path)

    if not p.exists() or p.stat().st_size == 0:
        return pd.DataFrame()

    try:
        return pd.read_csv(p)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def safe_read_json(path: str | Path, default: Any | None = None) -> Any:
    p = Path(path)

    if default is None:
        default = {}

    if not p.exists() or p.stat().st_size == 0:
        return default

    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default
