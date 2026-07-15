"""Incremental-value validation for morphology field conditions.

This module tests whether field dynamics add predictive value beyond static
morphology cluster membership.

Controls:
- same fold;
- same asset;
- same direction;
- same morphology cluster;
- non-overlapping event selection;
- transaction-cost adjustment;
- block-bootstrap confidence intervals;
- permutation tests;
- Benjamini-Hochberg multiple-testing correction.

Research only. No portfolio intents or execution actions are emitted.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


FIELD_CONDITIONS = (
    "HIGH_PREDICTABILITY",
    "HIGH_EXPANSION",
    "HIGH_CONTRACTION",
    "HIGH_ROTATION",
    "HIGH_STRAIN",
    "COMBINED_OPPORTUNITY",
)


@dataclass(frozen=True, slots=True)
class FieldIncrementalValueConfig:
    horizon_bars: int = 16
    transaction_cost_bps: float = 8.0
    minimum_condition_observations: int = 30
    minimum_control_observations: int = 30
    minimum_cluster_observations: int = 60
    minimum_valid_folds: int = 8
    minimum_positive_uplift_rate: float = 0.60
    non_overlap_bars: int = 16
    bootstrap_iterations: int = 1_000
    permutation_iterations: int = 1_000
    bootstrap_block_size: int = 4
    random_seed: int = 33
    significance_level: float = 0.05
    multiple_testing_alpha: float = 0.10

    def __post_init__(self) -> None:
        integer_fields = (
            "horizon_bars",
            "minimum_condition_observations",
            "minimum_control_observations",
            "minimum_cluster_observations",
            "minimum_valid_folds",
            "non_overlap_bars",
            "bootstrap_iterations",
            "permutation_iterations",
            "bootstrap_block_size",
        )

        for name in integer_fields:
            if int(getattr(self, name)) < 1:
                raise ValueError(
                    f"{name} must be positive."
                )

        if (
            not math.isfinite(self.transaction_cost_bps)
            or self.transaction_cost_bps < 0.0
        ):
            raise ValueError(
                "transaction_cost_bps must be finite and nonnegative."
            )

        for name in (
            "minimum_positive_uplift_rate",
            "significance_level",
            "multiple_testing_alpha",
        ):
            value = float(getattr(self, name))

            if not 0.0 < value < 1.0:
                raise ValueError(
                    f"{name} must be between zero and one."
                )


def load_incremental_scores(
    path: str | Path,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "timestamp",
        "fold_id",
        "morphology_cluster_id",
        "morphology_cluster",
        "field_supported",
        "field_high_predictability",
        "field_high_expansion",
        "field_high_contraction",
        "field_high_rotation",
        "field_high_strain",
        "field_combined_opportunity",
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            f"Field score file missing required columns: {missing}"
        )

    frame = frame.copy()

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        utc=True,
        errors="coerce",
    )

    frame["fold_id"] = pd.to_numeric(
        frame["fold_id"],
        errors="coerce",
    )

    frame["morphology_cluster_id"] = pd.to_numeric(
        frame["morphology_cluster_id"],
        errors="coerce",
    )

    boolean_columns = (
        "field_supported",
        "field_high_predictability",
        "field_high_expansion",
        "field_high_contraction",
        "field_high_rotation",
        "field_high_strain",
        "field_combined_opportunity",
    )

    for column in boolean_columns:
        frame[column] = (
            frame[column]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({
                "true": True,
                "false": False,
                "1": True,
                "0": False,
            })
            .fillna(False)
        )

    frame = frame.dropna(
        subset=[
            "timestamp",
            "fold_id",
            "morphology_cluster_id",
        ]
    )

    frame["fold_id"] = (
        frame["fold_id"].astype(int)
    )

    frame["morphology_cluster_id"] = (
        frame["morphology_cluster_id"].astype(int)
    )

    return (
        frame.sort_values(
            [
                "fold_id",
                "timestamp",
            ],
            kind="stable",
        )
        .drop_duplicates(
            subset=[
                "fold_id",
                "timestamp",
            ],
            keep="last",
        )
        .reset_index(drop=True)
    )


def load_incremental_outcomes(
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
            f"Outcome file missing required columns: {missing}"
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

    numeric_columns = required - {
        "timestamp",
        "asset",
    }

    for column in numeric_columns:
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


def condition_column(
    condition_name: str,
) -> str:
    mapping = {
        "HIGH_PREDICTABILITY":
            "field_high_predictability",
        "HIGH_EXPANSION":
            "field_high_expansion",
        "HIGH_CONTRACTION":
            "field_high_contraction",
        "HIGH_ROTATION":
            "field_high_rotation",
        "HIGH_STRAIN":
            "field_high_strain",
        "COMBINED_OPPORTUNITY":
            "field_combined_opportunity",
    }

    if condition_name not in mapping:
        raise ValueError(
            f"Unknown field condition: {condition_name}"
        )

    return mapping[condition_name]


def infer_base_bar_interval(
    frame: pd.DataFrame,
) -> pd.Timedelta:
    """Infer the underlying market-bar cadence from a complete population."""
    if frame.empty or "timestamp" not in frame.columns:
        return pd.Timedelta(minutes=15)

    timestamps = (
        pd.to_datetime(
            frame["timestamp"],
            utc=True,
            errors="coerce",
        )
        .dropna()
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    if len(timestamps) < 2:
        return pd.Timedelta(minutes=15)

    differences = (
        timestamps.diff()
        .dropna()
    )

    positive = differences[
        differences.gt(
            pd.Timedelta(0)
        )
    ]

    if positive.empty:
        return pd.Timedelta(minutes=15)

    # The smallest recurring positive difference represents the original
    # bar cadence better than the median after condition filtering.
    nanoseconds = (
        positive.astype("timedelta64[ns]")
        .astype("int64")
    )

    counts = nanoseconds.value_counts()

    most_common = int(
        counts.index[0]
    )

    minimum = int(
        nanoseconds.min()
    )

    # Prefer the minimum observed cadence when it is reasonably close to the
    # modal cadence. This protects irregular data while preserving 15m bars.
    selected = (
        minimum
        if minimum <= most_common
        else most_common
    )

    return pd.to_timedelta(
        selected,
        unit="ns",
    )


def select_non_overlapping(
    frame: pd.DataFrame,
    *,
    bars: int,
    bar_interval: pd.Timedelta | None = None,
) -> pd.DataFrame:
    """Greedily retain observations separated by a fixed number of base bars.

    `bar_interval` must be inferred from the unsplit fold/asset population.
    Inferring it from a sparse condition subset causes sampling aliasing.
    """
    if frame.empty:
        return frame.copy()

    ordered = (
        frame.sort_values(
            "timestamp",
            kind="stable",
        )
        .reset_index(drop=True)
    )

    timestamps = pd.to_datetime(
        ordered["timestamp"],
        utc=True,
        errors="coerce",
    )

    valid = timestamps.notna()

    if not valid.all():
        ordered = (
            ordered.loc[valid]
            .reset_index(drop=True)
        )

        timestamps = (
            timestamps.loc[valid]
            .reset_index(drop=True)
        )

    if ordered.empty:
        return ordered

    interval = (
        bar_interval
        if bar_interval is not None
        else infer_base_bar_interval(
            ordered
        )
    )

    if (
        pd.isna(interval)
        or interval <= pd.Timedelta(0)
    ):
        interval = pd.Timedelta(
            minutes=15
        )

    minimum_gap_ns = int(
        interval.value
        * int(bars)
    )

    timestamp_ns = (
        timestamps.to_numpy(
            dtype="datetime64[ns]"
        )
        .astype(
            np.int64,
            copy=False,
        )
    )

    selected_positions = np.empty(
        len(timestamp_ns),
        dtype=np.int64,
    )

    selected_count = 0
    last_timestamp_ns: int | None = None

    for position, timestamp_value in enumerate(
        timestamp_ns
    ):
        current = int(
            timestamp_value
        )

        if (
            last_timestamp_ns is None
            or current - last_timestamp_ns
            >= minimum_gap_ns
        ):
            selected_positions[
                selected_count
            ] = position

            selected_count += 1
            last_timestamp_ns = current

    return (
        ordered.iloc[
            selected_positions[
                :selected_count
            ]
        ]
        .reset_index(drop=True)
    )


def return_columns(
    *,
    direction: str,
    horizon_bars: int,
) -> tuple[str, str, str]:
    if direction == "LONG":
        return (
            f"forward_return_{horizon_bars}",
            f"long_mfe_{horizon_bars}",
            f"long_mae_{horizon_bars}",
        )

    if direction == "SHORT":
        return (
            f"short_return_{horizon_bars}",
            f"short_mfe_{horizon_bars}",
            f"short_mae_{horizon_bars}",
        )

    raise ValueError(
        f"Unsupported direction: {direction}"
    )


def cost_adjusted_returns(
    frame: pd.DataFrame,
    *,
    direction: str,
    horizon_bars: int,
    transaction_cost_bps: float,
) -> pd.Series:
    return_column, _, _ = return_columns(
        direction=direction,
        horizon_bars=horizon_bars,
    )

    values = pd.to_numeric(
        frame[return_column],
        errors="coerce",
    )

    cost = (
        transaction_cost_bps
        / 10_000.0
    )

    return (
        values - cost
    ).dropna()


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


def sample_metrics(
    frame: pd.DataFrame,
    *,
    direction: str,
    config: FieldIncrementalValueConfig,
) -> dict[str, float]:
    return_column, mfe_column, mae_column = (
        return_columns(
            direction=direction,
            horizon_bars=config.horizon_bars,
        )
    )

    raw = pd.to_numeric(
        frame[return_column],
        errors="coerce",
    ).dropna()

    adjusted = cost_adjusted_returns(
        frame,
        direction=direction,
        horizon_bars=config.horizon_bars,
        transaction_cost_bps=(
            config.transaction_cost_bps
        ),
    )

    mfe = pd.to_numeric(
        frame[mfe_column],
        errors="coerce",
    ).dropna()

    mae = pd.to_numeric(
        frame[mae_column],
        errors="coerce",
    ).dropna()

    if adjusted.empty:
        return {
            "observation_count": 0,
            "raw_mean_return": 0.0,
            "net_mean_return": 0.0,
            "net_median_return": 0.0,
            "net_win_rate": 0.0,
            "mean_mfe": 0.0,
            "mean_mae": 0.0,
            "profit_factor": 0.0,
            "return_to_mae": 0.0,
        }

    mean_mae = (
        float(mae.mean())
        if len(mae)
        else 0.0
    )

    net_mean = float(
        adjusted.mean()
    )

    return {
        "observation_count":
            int(len(adjusted)),
        "raw_mean_return":
            float(raw.mean())
            if len(raw)
            else 0.0,
        "net_mean_return":
            net_mean,
        "net_median_return":
            float(adjusted.median()),
        "net_win_rate":
            float(
                (
                    adjusted > 0.0
                ).mean()
            ),
        "mean_mfe":
            float(mfe.mean())
            if len(mfe)
            else 0.0,
        "mean_mae":
            mean_mae,
        "profit_factor":
            profit_factor(
                adjusted
            ),
        "return_to_mae":
            (
                net_mean
                / abs(mean_mae)
                if mean_mae != 0.0
                else 0.0
            ),
    }


def matched_cluster_samples(
    frame: pd.DataFrame,
    *,
    condition_name: str,
    config: FieldIncrementalValueConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    column = condition_column(
        condition_name
    )

    supported = frame[
        frame[
            "field_supported"
        ].astype(bool)
    ].copy()

    condition_rows = supported[
        supported[column].astype(bool)
    ].copy()

    control_rows = supported[
        ~supported[column].astype(bool)
    ].copy()

    valid_clusters = []

    for cluster_id, cluster_frame in (
        supported.groupby(
            "morphology_cluster_id",
            observed=True,
        )
    ):
        condition_count = int(
            cluster_frame[
                column
            ].astype(bool).sum()
        )

        control_count = int(
            (
                ~cluster_frame[
                    column
                ].astype(bool)
            ).sum()
        )

        total = int(
            len(cluster_frame)
        )

        if (
            condition_count
            >= config.minimum_condition_observations
            and control_count
            >= config.minimum_control_observations
            and total
            >= config.minimum_cluster_observations
        ):
            valid_clusters.append(
                int(cluster_id)
            )

    condition_rows = condition_rows[
        condition_rows[
            "morphology_cluster_id"
        ].isin(valid_clusters)
    ]

    control_rows = control_rows[
        control_rows[
            "morphology_cluster_id"
        ].isin(valid_clusters)
    ]

    return (
        condition_rows,
        control_rows,
    )


def cluster_weighted_uplift(
    condition_rows: pd.DataFrame,
    control_rows: pd.DataFrame,
    *,
    direction: str,
    config: FieldIncrementalValueConfig,
) -> tuple[float, pd.DataFrame]:
    cluster_rows = []

    condition_groups = {
        int(cluster_id): group
        for cluster_id, group in
        condition_rows.groupby(
            "morphology_cluster_id",
            observed=True,
        )
    }

    control_groups = {
        int(cluster_id): group
        for cluster_id, group in
        control_rows.groupby(
            "morphology_cluster_id",
            observed=True,
        )
    }

    shared_clusters = sorted(
        set(condition_groups)
        & set(control_groups)
    )

    for cluster_id in shared_clusters:
        condition_metrics = sample_metrics(
            condition_groups[cluster_id],
            direction=direction,
            config=config,
        )

        control_metrics = sample_metrics(
            control_groups[cluster_id],
            direction=direction,
            config=config,
        )

        weight = min(
            condition_metrics[
                "observation_count"
            ],
            control_metrics[
                "observation_count"
            ],
        )

        if weight <= 0:
            continue

        cluster_rows.append({
            "morphology_cluster_id":
                int(cluster_id),
            "condition_observations":
                int(
                    condition_metrics[
                        "observation_count"
                    ]
                ),
            "control_observations":
                int(
                    control_metrics[
                        "observation_count"
                    ]
                ),
            "matched_weight":
                int(weight),
            "condition_net_mean_return":
                condition_metrics[
                    "net_mean_return"
                ],
            "control_net_mean_return":
                control_metrics[
                    "net_mean_return"
                ],
            "cluster_uplift":
                (
                    condition_metrics[
                        "net_mean_return"
                    ]
                    - control_metrics[
                        "net_mean_return"
                    ]
                ),
            "condition_win_rate":
                condition_metrics[
                    "net_win_rate"
                ],
            "control_win_rate":
                control_metrics[
                    "net_win_rate"
                ],
        })

    details = pd.DataFrame(
        cluster_rows
    )

    if details.empty:
        return 0.0, details

    uplift = float(
        np.average(
            details[
                "cluster_uplift"
            ],
            weights=details[
                "matched_weight"
            ],
        )
    )

    return uplift, details


def moving_block_indices(
    count: int,
    *,
    block_size: int,
    rng: np.random.Generator,
) -> np.ndarray:
    if count <= 0:
        return np.asarray(
            [],
            dtype=int,
        )

    if count <= block_size:
        return rng.integers(
            0,
            count,
            size=count,
        )

    indices = []

    while len(indices) < count:
        start = int(
            rng.integers(
                0,
                count - block_size + 1,
            )
        )

        indices.extend(
            range(
                start,
                start + block_size,
            )
        )

    return np.asarray(
        indices[:count],
        dtype=int,
    )


def bootstrap_uplift_interval(
    condition_rows: pd.DataFrame,
    control_rows: pd.DataFrame,
    *,
    direction: str,
    config: FieldIncrementalValueConfig,
    rng: np.random.Generator,
) -> tuple[float, float]:
    values = []

    for _ in range(
        config.bootstrap_iterations
    ):
        condition_sample_parts = []
        control_sample_parts = []

        for cluster_id, group in (
            condition_rows.groupby(
                "morphology_cluster_id",
                observed=True,
            )
        ):
            indices = moving_block_indices(
                len(group),
                block_size=(
                    config.bootstrap_block_size
                ),
                rng=rng,
            )

            condition_sample_parts.append(
                group.iloc[indices]
            )

        for cluster_id, group in (
            control_rows.groupby(
                "morphology_cluster_id",
                observed=True,
            )
        ):
            indices = moving_block_indices(
                len(group),
                block_size=(
                    config.bootstrap_block_size
                ),
                rng=rng,
            )

            control_sample_parts.append(
                group.iloc[indices]
            )

        condition_sample = pd.concat(
            condition_sample_parts,
            ignore_index=True,
        )

        control_sample = pd.concat(
            control_sample_parts,
            ignore_index=True,
        )

        uplift, _ = cluster_weighted_uplift(
            condition_sample,
            control_sample,
            direction=direction,
            config=config,
        )

        values.append(uplift)

    lower = float(
        np.quantile(
            values,
            config.significance_level / 2.0,
        )
    )

    upper = float(
        np.quantile(
            values,
            1.0
            - config.significance_level / 2.0,
        )
    )

    return lower, upper


def permutation_p_value(
    frame: pd.DataFrame,
    *,
    condition_name: str,
    direction: str,
    observed_uplift: float,
    config: FieldIncrementalValueConfig,
    rng: np.random.Generator,
) -> float:
    column = condition_column(
        condition_name
    )

    supported = frame[
        frame[
            "field_supported"
        ].astype(bool)
    ].copy()

    extreme = 0
    valid_iterations = 0

    for _ in range(
        config.permutation_iterations
    ):
        permuted = supported.copy()

        permuted[
            "_permuted_condition"
        ] = False

        for _, group in (
            supported.groupby(
                "morphology_cluster_id",
                observed=True,
            )
        ):
            labels = (
                group[column]
                .astype(bool)
                .to_numpy()
                .copy()
            )

            rng.shuffle(labels)

            permuted.loc[
                group.index,
                "_permuted_condition",
            ] = labels

        condition_rows = permuted[
            permuted[
                "_permuted_condition"
            ].astype(bool)
        ]

        control_rows = permuted[
            ~permuted[
                "_permuted_condition"
            ].astype(bool)
        ]

        uplift, details = cluster_weighted_uplift(
            condition_rows,
            control_rows,
            direction=direction,
            config=config,
        )

        if details.empty:
            continue

        valid_iterations += 1

        if uplift >= observed_uplift:
            extreme += 1

    return (
        (extreme + 1)
        / (valid_iterations + 1)
        if valid_iterations
        else 1.0
    )


def evaluate_incremental_value(
    joined: pd.DataFrame,
    *,
    config: FieldIncrementalValueConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(
        config.random_seed
    )

    evaluation_rows = []
    cluster_detail_rows = []

    for fold_id, fold_frame in (
        joined.groupby(
            "fold_id",
            sort=True,
            observed=True,
        )
    ):
        for asset, asset_frame in (
            fold_frame.groupby(
                "asset",
                sort=True,
                observed=True,
            )
        ):
            for direction in (
                "LONG",
                "SHORT",
            ):
                base_bar_interval = infer_base_bar_interval(
                    asset_frame
                )

                for condition_name in (
                    FIELD_CONDITIONS
                ):
                    raw_condition_rows, raw_control_rows = (
                        matched_cluster_samples(
                            asset_frame,
                            condition_name=(
                                condition_name
                            ),
                            config=config,
                        )
                    )

                    condition_rows = (
                        select_non_overlapping(
                            raw_condition_rows,
                            bars=(
                                config.non_overlap_bars
                            ),
                            bar_interval=(
                                base_bar_interval
                            ),
                        )
                    )

                    control_rows = (
                        select_non_overlapping(
                            raw_control_rows,
                            bars=(
                                config.non_overlap_bars
                            ),
                            bar_interval=(
                                base_bar_interval
                            ),
                        )
                    )

                    condition_counts = (
                        condition_rows.groupby(
                            "morphology_cluster_id",
                            observed=True,
                        )
                        .size()
                    )

                    control_counts = (
                        control_rows.groupby(
                            "morphology_cluster_id",
                            observed=True,
                        )
                        .size()
                    )

                    shared_clusters = sorted(
                        set(condition_counts.index)
                        & set(control_counts.index)
                    )

                    valid_clusters = [
                        int(cluster_id)
                        for cluster_id in shared_clusters
                        if (
                            int(
                                condition_counts.loc[
                                    cluster_id
                                ]
                            )
                            >= config.minimum_condition_observations
                            and int(
                                control_counts.loc[
                                    cluster_id
                                ]
                            )
                            >= config.minimum_control_observations
                            and (
                                int(
                                    condition_counts.loc[
                                        cluster_id
                                    ]
                                )
                                + int(
                                    control_counts.loc[
                                        cluster_id
                                    ]
                                )
                            )
                            >= config.minimum_cluster_observations
                        )
                    ]

                    condition_rows = condition_rows[
                        condition_rows[
                            "morphology_cluster_id"
                        ].isin(valid_clusters)
                    ]

                    control_rows = control_rows[
                        control_rows[
                            "morphology_cluster_id"
                        ].isin(valid_clusters)
                    ]

                    if (
                        len(condition_rows)
                        < config.minimum_condition_observations
                        or len(control_rows)
                        < config.minimum_control_observations
                    ):
                        continue

                    matched_non_overlapping = (
                        pd.concat(
                            [
                                condition_rows,
                                control_rows,
                            ],
                            ignore_index=True,
                        )
                        .sort_values(
                            "timestamp",
                            kind="stable",
                        )
                        .reset_index(drop=True)
                    )

                    uplift, cluster_details = (
                        cluster_weighted_uplift(
                            condition_rows,
                            control_rows,
                            direction=direction,
                            config=config,
                        )
                    )

                    if cluster_details.empty:
                        continue

                    condition_metrics = (
                        sample_metrics(
                            condition_rows,
                            direction=direction,
                            config=config,
                        )
                    )

                    control_metrics = (
                        sample_metrics(
                            control_rows,
                            direction=direction,
                            config=config,
                        )
                    )

                    ci_low, ci_high = (
                        bootstrap_uplift_interval(
                            condition_rows,
                            control_rows,
                            direction=direction,
                            config=config,
                            rng=rng,
                        )
                    )

                    p_value = permutation_p_value(
                        matched_non_overlapping,
                        condition_name=(
                            condition_name
                        ),
                        direction=direction,
                        observed_uplift=uplift,
                        config=config,
                        rng=rng,
                    )

                    evaluation_rows.append({
                        "fold_id":
                            int(fold_id),
                        "asset":
                            str(asset),
                        "direction":
                            direction,
                        "condition_name":
                            condition_name,
                        "condition_observations":
                            int(
                                condition_metrics[
                                    "observation_count"
                                ]
                            ),
                        "control_observations":
                            int(
                                control_metrics[
                                    "observation_count"
                                ]
                            ),
                        "matched_cluster_count":
                            int(
                                len(
                                    cluster_details
                                )
                            ),
                        "condition_net_mean_return":
                            condition_metrics[
                                "net_mean_return"
                            ],
                        "control_net_mean_return":
                            control_metrics[
                                "net_mean_return"
                            ],
                        "cluster_matched_uplift":
                            uplift,
                        "condition_net_win_rate":
                            condition_metrics[
                                "net_win_rate"
                            ],
                        "control_net_win_rate":
                            control_metrics[
                                "net_win_rate"
                            ],
                        "condition_profit_factor":
                            condition_metrics[
                                "profit_factor"
                            ],
                        "control_profit_factor":
                            control_metrics[
                                "profit_factor"
                            ],
                        "condition_return_to_mae":
                            condition_metrics[
                                "return_to_mae"
                            ],
                        "control_return_to_mae":
                            control_metrics[
                                "return_to_mae"
                            ],
                        "uplift_ci_low":
                            ci_low,
                        "uplift_ci_high":
                            ci_high,
                        "permutation_p_value":
                            p_value,
                        "significant_positive":
                            bool(
                                ci_low > 0.0
                                and p_value
                                <= config.significance_level
                            ),
                    })

                    details = (
                        cluster_details.copy()
                    )

                    details[
                        "fold_id"
                    ] = int(fold_id)

                    details["asset"] = str(
                        asset
                    )

                    details[
                        "direction"
                    ] = direction

                    details[
                        "condition_name"
                    ] = condition_name

                    cluster_detail_rows.append(
                        details
                    )

    evaluations = pd.DataFrame(
        evaluation_rows
    )

    cluster_details = (
        pd.concat(
            cluster_detail_rows,
            ignore_index=True,
        )
        if cluster_detail_rows
        else pd.DataFrame()
    )

    return evaluations, cluster_details


def benjamini_hochberg(
    p_values: pd.Series,
) -> pd.Series:
    values = pd.to_numeric(
        p_values,
        errors="coerce",
    ).fillna(1.0).to_numpy()

    count = len(values)

    if count == 0:
        return pd.Series(
            dtype=float
        )

    order = np.argsort(
        values
    )

    ranked = values[order]

    adjusted = np.empty(
        count,
        dtype=float,
    )

    running = 1.0

    for reverse_index in range(
        count - 1,
        -1,
        -1,
    ):
        rank = reverse_index + 1

        candidate = (
            ranked[reverse_index]
            * count
            / rank
        )

        running = min(
            running,
            candidate,
        )

        adjusted[
            order[reverse_index]
        ] = min(
            running,
            1.0,
        )

    return pd.Series(
        adjusted,
        index=p_values.index,
    )


def summarize_incremental_value(
    evaluations: pd.DataFrame,
    *,
    config: FieldIncrementalValueConfig,
) -> pd.DataFrame:
    if evaluations.empty:
        return pd.DataFrame()

    rows = []

    dimensions = [
        "asset",
        "direction",
        "condition_name",
    ]

    for keys, group in evaluations.groupby(
        dimensions,
        sort=True,
        observed=True,
    ):
        asset, direction, condition_name = (
            keys
        )

        weights = (
            group[
                "condition_observations"
            ]
            .clip(lower=1)
        )

        weighted_uplift = float(
            np.average(
                group[
                    "cluster_matched_uplift"
                ],
                weights=weights,
            )
        )

        weighted_condition_return = float(
            np.average(
                group[
                    "condition_net_mean_return"
                ],
                weights=weights,
            )
        )

        positive_folds = int(
            group[
                "cluster_matched_uplift"
            ].gt(0.0).sum()
        )

        significant_folds = int(
            group[
                "significant_positive"
            ].astype(bool).sum()
        )

        combined_p = float(
            min(
                1.0,
                group[
                    "permutation_p_value"
                ].mean(),
            )
        )

        rows.append({
            "asset":
                str(asset),
            "direction":
                str(direction),
            "condition_name":
                str(condition_name),
            "valid_fold_count":
                int(len(group)),
            "total_condition_observations":
                int(
                    group[
                        "condition_observations"
                    ].sum()
                ),
            "total_control_observations":
                int(
                    group[
                        "control_observations"
                    ].sum()
                ),
            "weighted_condition_net_return":
                weighted_condition_return,
            "weighted_cluster_matched_uplift":
                weighted_uplift,
            "positive_uplift_fold_count":
                positive_folds,
            "positive_uplift_fold_rate":
                (
                    positive_folds
                    / len(group)
                ),
            "significant_positive_fold_count":
                significant_folds,
            "mean_permutation_p_value":
                combined_p,
            "mean_condition_profit_factor":
                float(
                    np.average(
                        group[
                            "condition_profit_factor"
                        ].replace(
                            [np.inf, -np.inf],
                            np.nan,
                        ).fillna(0.0),
                        weights=weights,
                    )
                ),
            "mean_condition_return_to_mae":
                float(
                    np.average(
                        group[
                            "condition_return_to_mae"
                        ],
                        weights=weights,
                    )
                ),
        })

    summary = pd.DataFrame(
        rows
    )

    summary[
        "bh_adjusted_p_value"
    ] = benjamini_hochberg(
        summary[
            "mean_permutation_p_value"
        ]
    )

    summary[
        "multiple_test_significant"
    ] = summary[
        "bh_adjusted_p_value"
    ].le(
        config.multiple_testing_alpha
    )

    summary[
        "incremental_value_candidate"
    ] = (
        summary[
            "valid_fold_count"
        ].ge(
            config.minimum_valid_folds
        )
        & summary[
            "weighted_condition_net_return"
        ].gt(0.0)
        & summary[
            "weighted_cluster_matched_uplift"
        ].gt(0.0)
        & summary[
            "positive_uplift_fold_rate"
        ].ge(
            config.minimum_positive_uplift_rate
        )
        & summary[
            "multiple_test_significant"
        ].astype(bool)
    )

    return (
        summary.sort_values(
            [
                "incremental_value_candidate",
                "weighted_cluster_matched_uplift",
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


def write_incremental_value_outputs(
    *,
    evaluations: pd.DataFrame,
    cluster_details: pd.DataFrame,
    summary: pd.DataFrame,
    config: FieldIncrementalValueConfig,
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
        "folds":
            directory
            / "field_incremental_value_folds.csv",
        "clusters":
            directory
            / "field_incremental_value_clusters.csv",
        "summary":
            directory
            / "field_incremental_value_summary.csv",
        "report":
            directory
            / "field_incremental_value_report.json",
    }

    evaluations.to_csv(
        outputs["folds"],
        index=False,
    )

    cluster_details.to_csv(
        outputs["clusters"],
        index=False,
    )

    summary.to_csv(
        outputs["summary"],
        index=False,
    )

    candidates = (
        summary[
            summary[
                "incremental_value_candidate"
            ].astype(bool)
        ]
        if not summary.empty
        else pd.DataFrame()
    )

    report = {
        "schema_version":
            "atlas.morphology_field_incremental_value.v1.1",
        "config":
            asdict(config),
        "fold_rows":
            int(len(evaluations)),
        "cluster_rows":
            int(len(cluster_details)),
        "summary_rows":
            int(len(summary)),
        "candidate_count":
            int(len(candidates)),
        "candidates":
            (
                candidates.to_dict(
                    orient="records"
                )
                if not candidates.empty
                else []
            ),
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
