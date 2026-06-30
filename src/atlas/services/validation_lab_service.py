"""Validation Lab service utilities."""

from __future__ import annotations

from typing import Any

import pandas as pd

from atlas.acf.builder import build_acf_profile
from atlas.research import (
    build_feature_correlation_audit,
    build_feature_variance_audit,
    build_profile_matrix_rows,
)


def build_validation_rows_for_profiles(profile_keys: list[str]) -> list[dict[str, Any]]:
    """Build research matrix rows for selected profile keys."""
    rows: list[dict[str, Any]] = []

    for name in profile_keys:
        acf = build_acf_profile(name)
        rows.extend(build_profile_matrix_rows(acf))

    return rows


def build_validation_variance_audit(rows: list[dict[str, Any]]) -> Any:
    """Build feature variance audit."""
    return build_feature_variance_audit(rows)


def build_validation_correlation_audit(rows: list[dict[str, Any]]) -> Any:
    """Build feature correlation audit."""
    return build_feature_correlation_audit(rows)


def build_pair_matrix_rows(name_a: str, name_b: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build matrix rows for two profiles."""
    acf_a = build_acf_profile(name_a)
    acf_b = build_acf_profile(name_b)

    rows_a = build_profile_matrix_rows(acf_a)
    rows_b = build_profile_matrix_rows(acf_b)

    return rows_a, rows_b


def rows_to_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Convert row dictionaries to dataframe."""
    return pd.DataFrame(rows)