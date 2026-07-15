"""Leakage-safe walk-forward validation for morphology field dynamics.

Each fold:

1. Fits a spatial morphology field using training timestamps only.
2. Freezes training-derived grid boundaries and field derivatives.
3. Maps later unseen morphology observations into the frozen field.
4. Marks unsupported regions as OUTSIDE_FIELD.
5. Evaluates asset-specific forward outcomes.
6. Compares static-cluster baselines with field-conditioned groups.

Research only. This module never creates portfolio intents or orders.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from atlas.investment.morphology_intelligence.field_dynamics import (
    MorphologyFieldConfig,
    build_field_cells,
    calculate_field_derivatives,
)


@dataclass(frozen=True, slots=True)
class FieldWalkForwardConfig:
    training_days: int = 180
    test_days: int = 30
    step_days: int = 30
    embargo_bars: int = 96
    minimum_training_timestamps: int = 5_000
    minimum_test_timestamps: int = 500
    minimum_test_observations: int = 30
    horizon_bars: int = 16
    grid_bins: int = 24
    minimum_cell_observations: int = 15
    smoothing_passes: int = 1
    maximum_support_distance: float = 2.5
    strong_predictability_quantile: float = 0.75
    expansion_quantile: float = 0.75
    contraction_quantile: float = 0.25
    curl_quantile: float = 0.75
    strain_quantile: float = 0.75

    def __post_init__(self) -> None:
        for name in (
            "training_days",
            "test_days",
            "step_days",
            "minimum_training_timestamps",
            "minimum_test_timestamps",
            "minimum_test_observations",
            "horizon_bars",
            "grid_bins",
            "minimum_cell_observations",
        ):
            if int(
                getattr(self, name)
            ) < 1:
                raise ValueError(
                    f"{name} must be positive."
                )

        if self.embargo_bars < 0:
            raise ValueError(
                "embargo_bars cannot be negative."
            )

        if (
            not math.isfinite(
                self.maximum_support_distance
            )
            or self.maximum_support_distance <= 0.0
        ):
            raise ValueError(
                "maximum_support_distance must be positive."
            )

        for name in (
            "strong_predictability_quantile",
            "expansion_quantile",
            "contraction_quantile",
            "curl_quantile",
            "strain_quantile",
        ):
            value = float(
                getattr(self, name)
            )

            if not 0.0 < value < 1.0:
                raise ValueError(
                    f"{name} must be between zero and one."
                )


def load_walk_forward_motion(
    path: str | Path,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "timestamp",
        "morphology_cluster_id",
        "morphology_cluster",
        "morphology_pc_1",
        "morphology_pc_2",
        "morphology_velocity_1",
        "morphology_velocity_2",
        "morphology_speed",
        "morphology_acceleration_magnitude",
        "morphology_curvature",
        "morphology_directional_stability",
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            f"Motion file missing required columns: {missing}"
        )

    frame = frame.copy()

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        utc=True,
        errors="coerce",
    )

    numeric_columns = sorted(
        required - {
            "timestamp",
            "morphology_cluster",
        }
    )

    for column in numeric_columns:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    frame = frame.dropna(
        subset=[
            "timestamp",
            "morphology_pc_1",
            "morphology_pc_2",
            "morphology_velocity_1",
            "morphology_velocity_2",
        ]
    )

    return (
        frame.sort_values(
            "timestamp",
            kind="stable",
        )
        .drop_duplicates(
            subset=["timestamp"],
            keep="last",
        )
        .reset_index(drop=True)
    )


def load_walk_forward_outcomes(
    path: str | Path,
    *,
    horizon_bars: int,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "timestamp",
        "asset",
        "morphology_cluster_id",
        f"forward_return_{horizon_bars}",
        f"short_return_{horizon_bars}",
        f"long_mfe_{horizon_bars}",
        f"long_mae_{horizon_bars}",
        f"short_mfe_{horizon_bars}",
        f"short_mae_{horizon_bars}",
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            f"Assignment file missing outcome columns: {missing}"
        )

    frame = frame.copy()

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        utc=True,
        errors="coerce",
    )

    frame["asset"] = (
        frame["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    for column in required - {
        "timestamp",
        "asset",
    }:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    return (
        frame.dropna(
            subset=[
                "timestamp",
                "asset",
                "morphology_cluster_id",
            ]
        )
        .sort_values(
            [
                "timestamp",
                "asset",
            ],
            kind="stable",
        )
        .drop_duplicates(
            subset=[
                "timestamp",
                "asset",
            ],
            keep="last",
        )
        .reset_index(drop=True)
    )


def finite_quantile_edges(
    values: pd.Series,
    *,
    bin_count: int,
) -> np.ndarray:
    numeric = pd.to_numeric(
        values,
        errors="coerce",
    ).dropna()

    if numeric.empty:
        raise ValueError(
            "Cannot fit grid on empty coordinates."
        )

    edges = np.quantile(
        numeric.to_numpy(
            dtype=float,
        ),
        np.linspace(
            0.0,
            1.0,
            bin_count + 1,
        ),
    )

    edges = np.unique(
        edges
    )

    if len(edges) < 3:
        minimum = float(
            numeric.min()
        )

        maximum = float(
            numeric.max()
        )

        if minimum == maximum:
            maximum = minimum + 1.0

        edges = np.linspace(
            minimum,
            maximum,
            bin_count + 1,
        )

    return edges


def assign_frozen_grid(
    frame: pd.DataFrame,
    *,
    x_edges: np.ndarray,
    y_edges: np.ndarray,
    training: bool,
) -> pd.DataFrame:
    result = frame.copy()

    x = pd.to_numeric(
        result["morphology_pc_1"],
        errors="coerce",
    )

    y = pd.to_numeric(
        result["morphology_pc_2"],
        errors="coerce",
    )

    supported = (
        x.ge(x_edges[0])
        & x.le(x_edges[-1])
        & y.ge(y_edges[0])
        & y.le(y_edges[-1])
    )

    if training:
        supported = supported.fillna(
            False
        )
    else:
        result[
            "field_inside_training_bounds"
        ] = supported.fillna(
            False
        )

    x_codes = pd.cut(
        x,
        bins=x_edges,
        labels=False,
        include_lowest=True,
    )

    y_codes = pd.cut(
        y,
        bins=y_edges,
        labels=False,
        include_lowest=True,
    )

    result["field_x_bin"] = x_codes
    result["field_y_bin"] = y_codes

    if training:
        result = result.dropna(
            subset=[
                "field_x_bin",
                "field_y_bin",
            ]
        )

    result["field_x_bin"] = (
        result["field_x_bin"]
        .fillna(-1)
        .astype(int)
    )

    result["field_y_bin"] = (
        result["field_y_bin"]
        .fillna(-1)
        .astype(int)
    )

    result["field_cell_id"] = np.where(
        result["field_x_bin"].ge(0)
        & result["field_y_bin"].ge(0),
        (
            result[
                "field_x_bin"
            ].astype(str)
            + ":"
            + result[
                "field_y_bin"
            ].astype(str)
        ),
        "OUTSIDE_FIELD",
    )

    return result


def fit_training_field(
    training_motion: pd.DataFrame,
    *,
    config: FieldWalkForwardConfig,
) -> tuple[
    pd.DataFrame,
    np.ndarray,
    np.ndarray,
    dict[str, float],
]:
    x_edges = finite_quantile_edges(
        training_motion[
            "morphology_pc_1"
        ],
        bin_count=config.grid_bins,
    )

    y_edges = finite_quantile_edges(
        training_motion[
            "morphology_pc_2"
        ],
        bin_count=config.grid_bins,
    )

    assigned = assign_frozen_grid(
        training_motion,
        x_edges=x_edges,
        y_edges=y_edges,
        training=True,
    )

    field_config = MorphologyFieldConfig(
        grid_bins=config.grid_bins,
        minimum_cell_observations=(
            config.minimum_cell_observations
        ),
        smoothing_passes=(
            config.smoothing_passes
        ),
    )

    cells = build_field_cells(
        assigned,
        config=field_config,
    )

    field = calculate_field_derivatives(
        cells,
        config=field_config,
    )

    eligible = field[
        field[
            "field_eligible"
        ].astype(bool)
    ].copy()

    if eligible.empty:
        thresholds = {
            "predictability_high": 1.0,
            "divergence_high": float("inf"),
            "divergence_low": float("-inf"),
            "curl_high": float("inf"),
            "strain_high": float("inf"),
        }
    else:
        thresholds = {
            "predictability_high":
                float(
                    eligible[
                        "field_predictability"
                    ].quantile(
                        config.strong_predictability_quantile
                    )
                ),
            "divergence_high":
                float(
                    eligible[
                        "field_divergence"
                    ].quantile(
                        config.expansion_quantile
                    )
                ),
            "divergence_low":
                float(
                    eligible[
                        "field_divergence"
                    ].quantile(
                        config.contraction_quantile
                    )
                ),
            "curl_high":
                float(
                    eligible[
                        "field_curl"
                    ].abs().quantile(
                        config.curl_quantile
                    )
                ),
            "strain_high":
                float(
                    eligible[
                        "field_strain_magnitude"
                    ].quantile(
                        config.strain_quantile
                    )
                ),
        }

    return (
        field,
        x_edges,
        y_edges,
        thresholds,
    )


def score_test_field(
    test_motion: pd.DataFrame,
    *,
    field: pd.DataFrame,
    x_edges: np.ndarray,
    y_edges: np.ndarray,
    thresholds: dict[str, float],
    config: FieldWalkForwardConfig,
) -> pd.DataFrame:
    scored = assign_frozen_grid(
        test_motion,
        x_edges=x_edges,
        y_edges=y_edges,
        training=False,
    )

    field_columns = [
        "field_x_bin",
        "field_y_bin",
        "field_cell_id",
        "field_eligible",
        "observation_count",
        "x_center",
        "y_center",
        "field_velocity_x",
        "field_velocity_y",
        "field_speed",
        "field_divergence",
        "field_curl",
        "field_strain_magnitude",
        "field_predictability",
        "field_flow_class",
    ]

    scored = scored.merge(
        field[
            field_columns
        ],
        on=[
            "field_x_bin",
            "field_y_bin",
            "field_cell_id",
        ],
        how="left",
        validate="many_to_one",
        suffixes=(
            "",
            "_field",
        ),
    )

    scored[
        "field_supported"
    ] = (
        scored[
            "field_inside_training_bounds"
        ].fillna(False)
        & scored[
            "field_eligible"
        ].fillna(False)
    )

    center_distance = np.sqrt(
        (
            scored[
                "morphology_pc_1"
            ]
            - scored[
                "x_center"
            ]
        ) ** 2
        + (
            scored[
                "morphology_pc_2"
            ]
            - scored[
                "y_center"
            ]
        ) ** 2
    )

    supported_cell_scale = (
        field[
            field["field_eligible"].astype(bool)
        ][
            [
                "x_center",
                "y_center",
            ]
        ]
    )

    if len(supported_cell_scale) > 1:
        coordinate_scale = float(
            np.sqrt(
                supported_cell_scale[
                    "x_center"
                ].var(ddof=0)
                + supported_cell_scale[
                    "y_center"
                ].var(ddof=0)
            )
        )
    else:
        coordinate_scale = 1.0

    coordinate_scale = max(
        coordinate_scale,
        1e-12,
    )

    scored[
        "field_support_distance"
    ] = (
        center_distance
        / coordinate_scale
    )

    scored[
        "field_supported"
    ] &= scored[
        "field_support_distance"
    ].le(
        config.maximum_support_distance
    )

    scored[
        "field_validation_state"
    ] = np.where(
        scored[
            "field_supported"
        ],
        scored[
            "field_flow_class"
        ].fillna(
            "UNCLASSIFIED"
        ),
        "OUTSIDE_FIELD",
    )

    supported = scored[
        "field_supported"
    ]

    scored[
        "field_high_predictability"
    ] = (
        supported
        & scored[
            "field_predictability"
        ].ge(
            thresholds[
                "predictability_high"
            ]
        )
    )

    scored[
        "field_high_expansion"
    ] = (
        supported
        & scored[
            "field_divergence"
        ].ge(
            thresholds[
                "divergence_high"
            ]
        )
    )

    scored[
        "field_high_contraction"
    ] = (
        supported
        & scored[
            "field_divergence"
        ].le(
            thresholds[
                "divergence_low"
            ]
        )
    )

    scored[
        "field_high_rotation"
    ] = (
        supported
        & scored[
            "field_curl"
        ].abs().ge(
            thresholds[
                "curl_high"
            ]
        )
    )

    scored[
        "field_high_strain"
    ] = (
        supported
        & scored[
            "field_strain_magnitude"
        ].ge(
            thresholds[
                "strain_high"
            ]
        )
    )

    scored[
        "field_combined_opportunity"
    ] = (
        scored[
            "field_high_predictability"
        ]
        & ~scored[
            "field_high_strain"
        ]
        & (
            scored[
                "field_high_expansion"
            ]
            | scored[
                "field_high_contraction"
            ]
        )
    )

    return scored


def build_walk_forward_folds(
    timestamps: pd.Series,
    *,
    config: FieldWalkForwardConfig,
) -> list[dict[str, Any]]:
    ordered = (
        pd.to_datetime(
            timestamps,
            utc=True,
            errors="coerce",
        )
        .dropna()
        .sort_values()
        .drop_duplicates()
    )

    if ordered.empty:
        return []

    first_timestamp = ordered.iloc[0]
    last_timestamp = ordered.iloc[-1]

    training_delta = pd.Timedelta(
        days=config.training_days
    )

    test_delta = pd.Timedelta(
        days=config.test_days
    )

    step_delta = pd.Timedelta(
        days=config.step_days
    )

    test_start = (
        first_timestamp
        + training_delta
    )

    folds = []
    fold_id = 1

    while test_start <= last_timestamp:
        train_start = (
            test_start
            - training_delta
        )

        test_end = min(
            test_start
            + test_delta,
            last_timestamp
            + pd.Timedelta(
                microseconds=1
            ),
        )

        folds.append({
            "fold_id":
                fold_id,
            "train_start":
                train_start,
            "train_end":
                test_start,
            "test_start":
                test_start,
            "test_end":
                test_end,
        })

        fold_id += 1
        test_start += step_delta

    return folds


def profit_factor(
    values: pd.Series,
) -> float:
    gains = float(
        values[
            values > 0.0
        ].sum()
    )

    losses = float(
        values[
            values < 0.0
        ].abs().sum()
    )

    if losses > 0.0:
        return gains / losses

    if gains > 0.0:
        return float("inf")

    return 0.0


def outcome_metrics(
    frame: pd.DataFrame,
    *,
    direction: str,
    horizon_bars: int,
) -> dict[str, float]:
    if direction == "LONG":
        return_column = (
            f"forward_return_{horizon_bars}"
        )

        mfe_column = (
            f"long_mfe_{horizon_bars}"
        )

        mae_column = (
            f"long_mae_{horizon_bars}"
        )
    else:
        return_column = (
            f"short_return_{horizon_bars}"
        )

        mfe_column = (
            f"short_mfe_{horizon_bars}"
        )

        mae_column = (
            f"short_mae_{horizon_bars}"
        )

    returns = pd.to_numeric(
        frame[return_column],
        errors="coerce",
    ).dropna()

    mfe = pd.to_numeric(
        frame[mfe_column],
        errors="coerce",
    ).dropna()

    mae = pd.to_numeric(
        frame[mae_column],
        errors="coerce",
    ).dropna()

    if returns.empty:
        return {
            "observation_count": 0,
            "mean_return": 0.0,
            "median_return": 0.0,
            "win_rate": 0.0,
            "mean_mfe": 0.0,
            "mean_mae": 0.0,
            "profit_factor": 0.0,
            "return_to_mae": 0.0,
        }

    mean_return = float(
        returns.mean()
    )

    mean_mae = float(
        mae.mean()
    ) if len(mae) else 0.0

    return {
        "observation_count":
            int(len(returns)),
        "mean_return":
            mean_return,
        "median_return":
            float(
                returns.median()
            ),
        "win_rate":
            float(
                (
                    returns > 0.0
                ).mean()
            ),
        "mean_mfe":
            float(
                mfe.mean()
            ) if len(mfe) else 0.0,
        "mean_mae":
            mean_mae,
        "profit_factor":
            profit_factor(
                returns
            ),
        "return_to_mae":
            (
                mean_return
                / abs(mean_mae)
                if mean_mae != 0.0
                else 0.0
            ),
    }


def evaluate_model_group(
    frame: pd.DataFrame,
    *,
    fold_id: int,
    asset: str,
    direction: str,
    model_name: str,
    condition_name: str,
    condition: pd.Series,
    horizon_bars: int,
    minimum_observations: int,
    baseline_metrics: dict[str, float],
) -> dict[str, Any]:
    selected = frame[
        condition.fillna(False)
    ]

    metrics = outcome_metrics(
        selected,
        direction=direction,
        horizon_bars=horizon_bars,
    )

    eligible = bool(
        metrics[
            "observation_count"
        ] >= minimum_observations
    )

    return {
        "fold_id":
            int(fold_id),
        "asset":
            asset,
        "direction":
            direction,
        "model_name":
            model_name,
        "condition_name":
            condition_name,
        "eligible":
            eligible,
        "coverage":
            float(
                len(selected)
                / max(
                    len(frame),
                    1,
                )
            ),
        **metrics,
        "baseline_mean_return":
            baseline_metrics[
                "mean_return"
            ],
        "baseline_win_rate":
            baseline_metrics[
                "win_rate"
            ],
        "mean_return_uplift":
            (
                metrics[
                    "mean_return"
                ]
                - baseline_metrics[
                    "mean_return"
                ]
            ),
        "win_rate_uplift":
            (
                metrics[
                    "win_rate"
                ]
                - baseline_metrics[
                    "win_rate"
                ]
            ),
    }


def evaluate_fold_outcomes(
    scored: pd.DataFrame,
    outcomes: pd.DataFrame,
    *,
    fold_id: int,
    config: FieldWalkForwardConfig,
) -> pd.DataFrame:
    joined = outcomes.merge(
        scored,
        on=[
            "timestamp",
            "morphology_cluster_id",
        ],
        how="inner",
        validate="many_to_one",
        suffixes=(
            "",
            "_field",
        ),
    )

    rows: list[dict[str, Any]] = []

    conditions = {
        "ALL":
            pd.Series(
                True,
                index=joined.index,
            ),
        "SUPPORTED_FIELD":
            joined[
                "field_supported"
            ].astype(bool),
        "HIGH_PREDICTABILITY":
            joined[
                "field_high_predictability"
            ].astype(bool),
        "HIGH_EXPANSION":
            joined[
                "field_high_expansion"
            ].astype(bool),
        "HIGH_CONTRACTION":
            joined[
                "field_high_contraction"
            ].astype(bool),
        "HIGH_ROTATION":
            joined[
                "field_high_rotation"
            ].astype(bool),
        "HIGH_STRAIN":
            joined[
                "field_high_strain"
            ].astype(bool),
        "COMBINED_OPPORTUNITY":
            joined[
                "field_combined_opportunity"
            ].astype(bool),
    }

    for asset, asset_frame in joined.groupby(
        "asset",
        sort=True,
        observed=True,
    ):
        for direction in (
            "LONG",
            "SHORT",
        ):
            baseline = outcome_metrics(
                asset_frame,
                direction=direction,
                horizon_bars=(
                    config.horizon_bars
                ),
            )

            for condition_name in conditions:
                condition = conditions[
                    condition_name
                ].reindex(
                    asset_frame.index,
                    fill_value=False,
                )

                model_name = (
                    "STATIC_BASELINE"
                    if condition_name == "ALL"
                    else "FIELD_CONDITIONED"
                )

                rows.append(
                    evaluate_model_group(
                        asset_frame,
                        fold_id=fold_id,
                        asset=str(asset),
                        direction=direction,
                        model_name=model_name,
                        condition_name=(
                            condition_name
                        ),
                        condition=condition,
                        horizon_bars=(
                            config.horizon_bars
                        ),
                        minimum_observations=(
                            config.minimum_test_observations
                        ),
                        baseline_metrics=baseline,
                    )
                )

    return pd.DataFrame(rows)


def run_field_walk_forward(
    *,
    motion: pd.DataFrame,
    outcomes: pd.DataFrame,
    config: FieldWalkForwardConfig,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    folds = build_walk_forward_folds(
        motion["timestamp"],
        config=config,
    )

    score_rows = []
    evaluation_rows = []

    for fold in folds:
        training = motion[
            motion[
                "timestamp"
            ].ge(
                fold[
                    "train_start"
                ]
            )
            & motion[
                "timestamp"
            ].lt(
                fold[
                    "train_end"
                ]
            )
        ].copy()

        testing = motion[
            motion[
                "timestamp"
            ].ge(
                fold[
                    "test_start"
                ]
            )
            & motion[
                "timestamp"
            ].lt(
                fold[
                    "test_end"
                ]
            )
        ].copy()

        if (
            len(training)
            < config.minimum_training_timestamps
            or len(testing)
            < config.minimum_test_timestamps
        ):
            continue

        field, x_edges, y_edges, thresholds = (
            fit_training_field(
                training,
                config=config,
            )
        )

        scored = score_test_field(
            testing,
            field=field,
            x_edges=x_edges,
            y_edges=y_edges,
            thresholds=thresholds,
            config=config,
        )

        scored["fold_id"] = int(
            fold["fold_id"]
        )

        scored["train_start"] = (
            fold["train_start"]
        )

        scored["train_end"] = (
            fold["train_end"]
        )

        scored["test_start"] = (
            fold["test_start"]
        )

        scored["test_end"] = (
            fold["test_end"]
        )

        score_rows.append(
            scored
        )

        embargo_duration = (
            testing[
                "timestamp"
            ]
            .sort_values()
            .diff()
            .dropna()
            .median()
        )

        if pd.isna(
            embargo_duration
        ):
            embargo_duration = (
                pd.Timedelta(
                    minutes=15
                )
            )

        label_end = (
            fold["test_end"]
            - embargo_duration
            * max(
                config.embargo_bars,
                config.horizon_bars,
            )
        )

        fold_outcomes = outcomes[
            outcomes[
                "timestamp"
            ].ge(
                fold[
                    "test_start"
                ]
            )
            & outcomes[
                "timestamp"
            ].lt(
                label_end
            )
        ].copy()

        evaluations = evaluate_fold_outcomes(
            scored,
            fold_outcomes,
            fold_id=int(
                fold["fold_id"]
            ),
            config=config,
        )

        evaluations[
            "train_start"
        ] = fold[
            "train_start"
        ]

        evaluations[
            "train_end"
        ] = fold[
            "train_end"
        ]

        evaluations[
            "test_start"
        ] = fold[
            "test_start"
        ]

        evaluations[
            "test_end"
        ] = fold[
            "test_end"
        ]

        evaluations[
            "training_timestamps"
        ] = int(
            len(training)
        )

        evaluations[
            "test_timestamps"
        ] = int(
            len(testing)
        )

        evaluation_rows.append(
            evaluations
        )

    scores = (
        pd.concat(
            score_rows,
            ignore_index=True,
        )
        if score_rows
        else pd.DataFrame()
    )

    evaluations = (
        pd.concat(
            evaluation_rows,
            ignore_index=True,
        )
        if evaluation_rows
        else pd.DataFrame()
    )

    return scores, evaluations


def summarize_field_validation(
    evaluations: pd.DataFrame,
) -> pd.DataFrame:
    if evaluations.empty:
        return pd.DataFrame()

    rows = []

    dimensions = [
        "asset",
        "direction",
        "model_name",
        "condition_name",
    ]

    for keys, group in evaluations.groupby(
        dimensions,
        sort=True,
        observed=True,
    ):
        (
            asset,
            direction,
            model_name,
            condition_name,
        ) = keys

        eligible = group[
            group["eligible"].astype(bool)
        ]

        total_observations = int(
            eligible[
                "observation_count"
            ].sum()
        )

        if (
            not eligible.empty
            and total_observations > 0
        ):
            weights = eligible[
                "observation_count"
            ]

            weighted_return = float(
                np.average(
                    eligible[
                        "mean_return"
                    ],
                    weights=weights,
                )
            )

            weighted_win_rate = float(
                np.average(
                    eligible[
                        "win_rate"
                    ],
                    weights=weights,
                )
            )

            weighted_uplift = float(
                np.average(
                    eligible[
                        "mean_return_uplift"
                    ],
                    weights=weights,
                )
            )

            weighted_win_uplift = float(
                np.average(
                    eligible[
                        "win_rate_uplift"
                    ],
                    weights=weights,
                )
            )

            positive_return_folds = int(
                eligible[
                    "mean_return"
                ].gt(0.0).sum()
            )

            positive_uplift_folds = int(
                eligible[
                    "mean_return_uplift"
                ].gt(0.0).sum()
            )
        else:
            weighted_return = 0.0
            weighted_win_rate = 0.0
            weighted_uplift = 0.0
            weighted_win_uplift = 0.0
            positive_return_folds = 0
            positive_uplift_folds = 0

        valid_fold_count = int(
            len(eligible)
        )

        rows.append({
            "asset":
                str(asset),
            "direction":
                str(direction),
            "model_name":
                str(model_name),
            "condition_name":
                str(condition_name),
            "fold_count":
                int(len(group)),
            "eligible_fold_count":
                valid_fold_count,
            "total_observations":
                total_observations,
            "mean_coverage":
                float(
                    eligible[
                        "coverage"
                    ].mean()
                ) if valid_fold_count else 0.0,
            "weighted_mean_return":
                weighted_return,
            "weighted_win_rate":
                weighted_win_rate,
            "weighted_mean_return_uplift":
                weighted_uplift,
            "weighted_win_rate_uplift":
                weighted_win_uplift,
            "positive_return_fold_count":
                positive_return_folds,
            "positive_uplift_fold_count":
                positive_uplift_folds,
            "positive_return_fold_rate":
                (
                    positive_return_folds
                    / valid_fold_count
                    if valid_fold_count
                    else 0.0
                ),
            "positive_uplift_fold_rate":
                (
                    positive_uplift_folds
                    / valid_fold_count
                    if valid_fold_count
                    else 0.0
                ),
            "research_candidate":
                bool(
                    valid_fold_count >= 3
                    and total_observations >= 100
                    and weighted_return > 0.0
                    and weighted_uplift > 0.0
                    and (
                        positive_uplift_folds
                        / valid_fold_count
                    ) >= 0.60
                ) if valid_fold_count else False,
        })

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "research_candidate",
                "weighted_mean_return_uplift",
                "positive_uplift_fold_rate",
            ],
            ascending=[
                False,
                False,
                False,
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def write_field_walk_forward_outputs(
    *,
    scores: pd.DataFrame,
    evaluations: pd.DataFrame,
    summary: pd.DataFrame,
    config: FieldWalkForwardConfig,
    output_dir: str | Path,
) -> dict[str, Path]:
    directory = Path(
        output_dir
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    outputs = {
        "scores":
            directory
            / "field_walk_forward_scores.csv",
        "folds":
            directory
            / "field_walk_forward_folds.csv",
        "summary":
            directory
            / "field_walk_forward_summary.csv",
        "report":
            directory
            / "field_walk_forward_report.json",
    }

    scores.to_csv(
        outputs["scores"],
        index=False,
    )

    evaluations.to_csv(
        outputs["folds"],
        index=False,
    )

    summary.to_csv(
        outputs["summary"],
        index=False,
    )

    candidates = (
        summary[
            summary[
                "research_candidate"
            ].astype(bool)
        ]
        if not summary.empty
        else pd.DataFrame()
    )

    report = {
        "schema_version":
            "atlas.morphology_field_walk_forward.v1",
        "config":
            asdict(config),
        "scored_timestamp_rows":
            int(len(scores)),
        "fold_evaluation_rows":
            int(len(evaluations)),
        "summary_rows":
            int(len(summary)),
        "research_candidate_count":
            int(len(candidates)),
        "research_candidates":
            candidates.to_dict(
                orient="records"
            ) if not candidates.empty else [],
    }

    outputs["report"].write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    return outputs
