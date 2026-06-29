"""Population service utilities."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles
from atlas.research.matrix import build_profile_matrix_rows
from atlas.research.validation import build_profile_feature_matrix


def load_population_matrix() -> pd.DataFrame:
    """Load all saved profiles into row-level research matrix."""
    rows: list[dict[str, Any]] = []

    for profile_key in list_saved_profiles():
        acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

        if not acf_path.exists():
            continue

        try:
            acf = json.loads(acf_path.read_text(encoding="utf-8"))
            rows.extend(build_profile_matrix_rows(acf))
        except Exception:
            continue

    return pd.DataFrame(rows)


def load_profile_feature_matrix() -> pd.DataFrame:
    """Load profile-level feature matrix."""
    return build_profile_feature_matrix(load_population_matrix())