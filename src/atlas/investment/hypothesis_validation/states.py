"""Point-in-time feature-state reconstruction."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class StateDefinition:
    """Training-derived state definition."""

    feature: str
    feature_type: str
    low_threshold: float | None = None
    high_threshold: float | None = None


def fit_state_definition(
    training: pd.DataFrame,
    *,
    feature: str,
) -> StateDefinition | None:
    """Learn state boundaries using training data only."""
    if (
        training is None
        or training.empty
        or feature not in training.columns
    ):
        return None

    numeric = pd.to_numeric(
        training[feature],
        errors="coerce",
    )

    numeric_coverage = float(
        numeric.notna().mean()
    )

    if numeric_coverage >= 0.80:
        valid = numeric.dropna()

        if valid.empty:
            return None

        low = float(
            valid.quantile(
                1.0 / 3.0
            )
        )

        high = float(
            valid.quantile(
                2.0 / 3.0
            )
        )

        return StateDefinition(
            feature=feature,
            feature_type=(
                "NUMERIC_TERCILE"
            ),
            low_threshold=low,
            high_threshold=high,
        )

    return StateDefinition(
        feature=feature,
        feature_type="CATEGORICAL",
    )


def apply_state_definition(
    frame: pd.DataFrame,
    definition: StateDefinition,
) -> pd.Series:
    """Apply a training-derived state definition."""
    feature = definition.feature

    if feature not in frame.columns:
        return pd.Series(
            "UNKNOWN",
            index=frame.index,
            dtype=object,
        )

    if (
        definition.feature_type
        == "CATEGORICAL"
    ):
        return (
            frame[feature]
            .fillna("UNKNOWN")
            .astype(str)
            .str.upper()
        )

    numeric = pd.to_numeric(
        frame[feature],
        errors="coerce",
    )

    result = pd.Series(
        "UNKNOWN",
        index=frame.index,
        dtype=object,
    )

    low = float(
        definition.low_threshold
    )

    high = float(
        definition.high_threshold
    )

    if abs(
        high - low
    ) <= 1e-12:
        result.loc[
            numeric.notna()
        ] = "MID"

        return result

    result.loc[
        numeric <= low
    ] = "LOW"

    result.loc[
        (
            numeric > low
        )
        & (
            numeric < high
        )
    ] = "MID"

    result.loc[
        numeric >= high
    ] = "HIGH"

    return result


def build_gate_mask(
    states: pd.Series,
    *,
    hypothesis_type: str,
    target_state: str,
) -> pd.Series:
    """Construct the gated candidate mask."""
    normalized_target = str(
        target_state
    ).upper()

    usable = states.ne(
        "UNKNOWN"
    )

    matches = (
        states.astype(str)
        .str.upper()
        .eq(
            normalized_target
        )
    )

    if (
        hypothesis_type
        == "FAILURE_MODE_GATE"
    ):
        return usable & ~matches

    if (
        hypothesis_type
        == "CONDITIONAL_OPPORTUNITY"
    ):
        return usable & matches

    return pd.Series(
        False,
        index=states.index,
        dtype=bool,
    )
