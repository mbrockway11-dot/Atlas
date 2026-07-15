"""Realized morphology trajectory research.

The engine extracts chronological sequences from learned morphology cluster
assignments and profiles their asset-specific future outcomes.

Research only:
- no order creation;
- no position sizing;
- no live execution;
- future outcomes are labels only and are never used to define trajectories.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


BASE_REQUIRED = {
    "timestamp",
    "asset",
    "morphology_cluster_id",
    "morphology_cluster",
}


@dataclass(frozen=True, slots=True)
class MorphologyTrajectoryConfig:
    sequence_lengths: tuple[int, ...] = (
        3,
        4,
        5,
        8,
    )
    outcome_horizons: tuple[int, ...] = (
        4,
        8,
        16,
        32,
        96,
    )
    minimum_observations: int = 30
    confidence_target: int = 500
    stride: int = 1
    compress_repeated_states: bool = False
    maximum_gap_multiple: float = 3.0
    risk_penalty: float = 0.50

    def __post_init__(self) -> None:
        lengths = tuple(
            sorted(
                set(
                    int(value)
                    for value
                    in self.sequence_lengths
                )
            )
        )

        horizons = tuple(
            sorted(
                set(
                    int(value)
                    for value
                    in self.outcome_horizons
                )
            )
        )

        if not lengths or any(
            value < 2
            for value in lengths
        ):
            raise ValueError(
                "sequence_lengths must contain integers >= 2."
            )

        if not horizons or any(
            value < 1
            for value in horizons
        ):
            raise ValueError(
                "outcome_horizons must contain positive integers."
            )

        if self.minimum_observations < 2:
            raise ValueError(
                "minimum_observations must be at least 2."
            )

        if self.confidence_target < 1:
            raise ValueError(
                "confidence_target must be positive."
            )

        if self.stride < 1:
            raise ValueError(
                "stride must be positive."
            )

        if (
            not math.isfinite(
                self.maximum_gap_multiple
            )
            or self.maximum_gap_multiple <= 1.0
        ):
            raise ValueError(
                "maximum_gap_multiple must exceed 1."
            )

        if (
            not math.isfinite(
                self.risk_penalty
            )
            or self.risk_penalty < 0.0
        ):
            raise ValueError(
                "risk_penalty must be finite and nonnegative."
            )


def load_trajectory_assignments(
    path: str | Path,
    *,
    config: MorphologyTrajectoryConfig = (
        MorphologyTrajectoryConfig()
    ),
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    required = set(
        BASE_REQUIRED
    )

    for horizon in config.outcome_horizons:
        required.update({
            f"forward_return_{horizon}",
            f"short_return_{horizon}",
            f"long_mfe_{horizon}",
            f"long_mae_{horizon}",
            f"short_mfe_{horizon}",
            f"short_mae_{horizon}",
        })

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            "Trajectory assignments are missing "
            f"required columns: {missing}"
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

    frame["morphology_cluster_id"] = (
        pd.to_numeric(
            frame[
                "morphology_cluster_id"
            ],
            errors="coerce",
        )
    )

    numeric_columns = []

    for horizon in config.outcome_horizons:
        numeric_columns.extend([
            f"forward_return_{horizon}",
            f"short_return_{horizon}",
            f"long_mfe_{horizon}",
            f"long_mae_{horizon}",
            f"short_mfe_{horizon}",
            f"short_mae_{horizon}",
        ])

    for column in numeric_columns:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    frame = frame.dropna(
        subset=[
            "timestamp",
            "asset",
            "morphology_cluster_id",
            "morphology_cluster",
        ]
    )

    frame[
        "morphology_cluster_id"
    ] = frame[
        "morphology_cluster_id"
    ].astype(int)

    return (
        frame.sort_values(
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


def build_timestamp_morphology(
    assignments: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "timestamp",
        "morphology_cluster_id",
        "morphology_cluster",
    ]

    optional_columns = [
        column
        for column in assignments.columns
        if column.startswith(
            "morphology_pc_"
        )
    ]

    frame = (
        assignments[
            columns + optional_columns
        ]
        .drop_duplicates(
            subset=["timestamp"],
            keep="first",
        )
        .sort_values(
            "timestamp",
            kind="stable",
        )
        .reset_index(drop=True)
    )

    cluster_counts = (
        assignments.groupby(
            "timestamp",
            observed=True,
        )[
            "morphology_cluster_id"
        ]
        .nunique()
    )

    if not cluster_counts.eq(1).all():
        raise ValueError(
            "Each timestamp must map to exactly one morphology cluster."
        )

    return frame


def infer_bar_interval(
    timestamps: pd.Series,
) -> pd.Timedelta:
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

    differences = (
        ordered.diff()
        .dropna()
    )

    differences = differences[
        differences.gt(
            pd.Timedelta(0)
        )
    ]

    if differences.empty:
        return pd.Timedelta(
            minutes=15
        )

    return differences.median()


def compress_consecutive_states(
    morphology: pd.DataFrame,
) -> pd.DataFrame:
    frame = morphology.copy()

    changed = (
        frame[
            "morphology_cluster_id"
        ]
        .ne(
            frame[
                "morphology_cluster_id"
            ].shift(1)
        )
    )

    run_id = changed.cumsum()

    rows = []

    for _, group in frame.groupby(
        run_id,
        sort=True,
        observed=True,
    ):
        last = group.iloc[-1].copy()

        last[
            "state_run_bars"
        ] = int(
            len(group)
        )

        last[
            "state_run_start"
        ] = group[
            "timestamp"
        ].iloc[0]

        rows.append(last)

    return (
        pd.DataFrame(rows)
        .reset_index(drop=True)
    )


def split_contiguous_segments(
    morphology: pd.DataFrame,
    *,
    maximum_gap_multiple: float,
) -> list[pd.DataFrame]:
    frame = morphology.sort_values(
        "timestamp",
        kind="stable",
    ).reset_index(drop=True)

    if frame.empty:
        return []

    interval = infer_bar_interval(
        frame["timestamp"]
    )

    maximum_gap = (
        interval
        * maximum_gap_multiple
    )

    gaps = (
        frame["timestamp"].diff()
    )

    segment_ids = (
        gaps.gt(maximum_gap)
        .fillna(False)
        .cumsum()
    )

    return [
        group.reset_index(drop=True)
        for _, group in frame.groupby(
            segment_ids,
            sort=True,
            observed=True,
        )
    ]


def trajectory_key(
    cluster_ids: Iterable[int],
) -> str:
    return "->".join(
        str(int(value))
        for value in cluster_ids
    )


def trajectory_identity(
    *,
    sequence_length: int,
    cluster_path: str,
) -> str:
    payload = (
        f"{int(sequence_length)}|"
        f"{cluster_path}"
    ).encode("utf-8")

    digest = hashlib.sha256(
        payload
    ).hexdigest()[:16]

    return (
        f"TRAJ-{sequence_length:02d}-"
        f"{digest}"
    )


def trajectory_shape_metrics(
    cluster_ids: list[int],
) -> dict[str, Any]:
    length = len(
        cluster_ids
    )

    switches = sum(
        left != right
        for left, right in zip(
            cluster_ids[:-1],
            cluster_ids[1:],
        )
    )

    repeated_steps = (
        max(
            length - 1 - switches,
            0,
        )
    )

    unique_states = len(
        set(cluster_ids)
    )

    returns_to_prior = 0

    for index in range(
        2,
        length,
    ):
        if (
            cluster_ids[index]
            == cluster_ids[index - 2]
            and cluster_ids[index]
            != cluster_ids[index - 1]
        ):
            returns_to_prior += 1

    persistence_ratio = (
        repeated_steps
        / max(
            length - 1,
            1,
        )
    )

    switching_ratio = (
        switches
        / max(
            length - 1,
            1,
        )
    )

    if unique_states == 1:
        shape = "PERSISTENT"
    elif returns_to_prior > 0:
        shape = "OSCILLATING"
    elif cluster_ids[0] == cluster_ids[-1]:
        shape = "RETURNING"
    elif unique_states == length:
        shape = "PROGRESSIVE"
    else:
        shape = "MIXED"

    return {
        "unique_state_count":
            int(unique_states),
        "switch_count":
            int(switches),
        "return_to_prior_count":
            int(returns_to_prior),
        "persistence_ratio":
            float(persistence_ratio),
        "switching_ratio":
            float(switching_ratio),
        "trajectory_shape":
            shape,
    }


def extract_trajectory_windows(
    morphology: pd.DataFrame,
    *,
    config: MorphologyTrajectoryConfig,
) -> pd.DataFrame:
    source = morphology.copy()

    if config.compress_repeated_states:
        source = (
            compress_consecutive_states(
                source
            )
        )

    segments = split_contiguous_segments(
        source,
        maximum_gap_multiple=(
            config.maximum_gap_multiple
        ),
    )

    rows: list[dict[str, Any]] = []

    for segment_id, segment in enumerate(
        segments
    ):
        for sequence_length in (
            config.sequence_lengths
        ):
            if len(segment) < sequence_length:
                continue

            final_start = (
                len(segment)
                - sequence_length
            )

            for start in range(
                0,
                final_start + 1,
                config.stride,
            ):
                stop = (
                    start
                    + sequence_length
                )

                window = segment.iloc[
                    start:stop
                ]

                cluster_ids = (
                    window[
                        "morphology_cluster_id"
                    ]
                    .astype(int)
                    .tolist()
                )

                cluster_names = (
                    window[
                        "morphology_cluster"
                    ]
                    .astype(str)
                    .tolist()
                )

                path = trajectory_key(
                    cluster_ids
                )

                metrics = (
                    trajectory_shape_metrics(
                        cluster_ids
                    )
                )

                row = {
                    "trajectory_id":
                        trajectory_identity(
                            sequence_length=(
                                sequence_length
                            ),
                            cluster_path=path,
                        ),
                    "sequence_length":
                        int(sequence_length),
                    "cluster_path":
                        path,
                    "cluster_name_path":
                        "->".join(
                            cluster_names
                        ),
                    "segment_id":
                        int(segment_id),
                    "window_start":
                        window[
                            "timestamp"
                        ].iloc[0],
                    "window_end":
                        window[
                            "timestamp"
                        ].iloc[-1],
                    "source_cluster_id":
                        int(
                            cluster_ids[0]
                        ),
                    "terminal_cluster_id":
                        int(
                            cluster_ids[-1]
                        ),
                    "source_cluster":
                        str(
                            cluster_names[0]
                        ),
                    "terminal_cluster":
                        str(
                            cluster_names[-1]
                        ),
                    **metrics,
                }

                rows.append(row)

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "window_end",
                "sequence_length",
                "cluster_path",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def attach_asset_outcomes(
    windows: pd.DataFrame,
    assignments: pd.DataFrame,
    *,
    config: MorphologyTrajectoryConfig,
) -> pd.DataFrame:
    outcome_columns = [
        "timestamp",
        "asset",
    ]

    for horizon in config.outcome_horizons:
        outcome_columns.extend([
            f"forward_return_{horizon}",
            f"short_return_{horizon}",
            f"long_mfe_{horizon}",
            f"long_mae_{horizon}",
            f"short_mfe_{horizon}",
            f"short_mae_{horizon}",
        ])

    outcomes = assignments[
        outcome_columns
    ].rename(
        columns={
            "timestamp":
                "window_end"
        }
    )

    result = windows.merge(
        outcomes,
        on="window_end",
        how="inner",
        validate="many_to_many",
    )

    return (
        result.sort_values(
            [
                "window_end",
                "sequence_length",
                "asset",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def safe_profit_factor(
    values: pd.Series,
) -> float:
    positive = values[
        values > 0.0
    ]

    negative = values[
        values < 0.0
    ].abs()

    gross_profit = float(
        positive.sum()
    )

    gross_loss = float(
        negative.sum()
    )

    if gross_loss > 0.0:
        return (
            gross_profit
            / gross_loss
        )

    if gross_profit > 0.0:
        return float("inf")

    return 0.0


def profile_trajectory_outcomes(
    trajectory_observations: pd.DataFrame,
    *,
    config: MorphologyTrajectoryConfig,
) -> pd.DataFrame:
    dimensions = [
        "trajectory_id",
        "sequence_length",
        "cluster_path",
        "cluster_name_path",
        "source_cluster_id",
        "terminal_cluster_id",
        "source_cluster",
        "terminal_cluster",
        "trajectory_shape",
        "unique_state_count",
        "switch_count",
        "return_to_prior_count",
        "persistence_ratio",
        "switching_ratio",
        "asset",
    ]

    rows: list[dict[str, Any]] = []

    grouped = trajectory_observations.groupby(
        dimensions,
        sort=True,
        observed=True,
        dropna=False,
    )

    for keys, group in grouped:
        row = dict(
            zip(
                dimensions,
                keys,
            )
        )

        count = int(
            len(group)
        )

        row[
            "observation_count"
        ] = count

        row[
            "timestamp_min"
        ] = group[
            "window_end"
        ].min().isoformat()

        row[
            "timestamp_max"
        ] = group[
            "window_end"
        ].max().isoformat()

        row[
            "confidence"
        ] = min(
            1.0,
            count
            / float(
                config.confidence_target
            ),
        )

        row[
            "eligible"
        ] = bool(
            count
            >= config.minimum_observations
        )

        best_direction = "FLAT"
        best_horizon = 0
        best_score = float("-inf")
        best_mean_return = 0.0
        best_win_rate = 0.0
        best_mfe = 0.0
        best_mae = 0.0
        best_profit_factor = 0.0

        for horizon in config.outcome_horizons:
            for direction in (
                "LONG",
                "SHORT",
            ):
                if direction == "LONG":
                    returns_column = (
                        f"forward_return_{horizon}"
                    )
                    mfe_column = (
                        f"long_mfe_{horizon}"
                    )
                    mae_column = (
                        f"long_mae_{horizon}"
                    )
                else:
                    returns_column = (
                        f"short_return_{horizon}"
                    )
                    mfe_column = (
                        f"short_mfe_{horizon}"
                    )
                    mae_column = (
                        f"short_mae_{horizon}"
                    )

                values = pd.to_numeric(
                    group[
                        returns_column
                    ],
                    errors="coerce",
                ).dropna()

                mfe_values = pd.to_numeric(
                    group[
                        mfe_column
                    ],
                    errors="coerce",
                ).dropna()

                mae_values = pd.to_numeric(
                    group[
                        mae_column
                    ],
                    errors="coerce",
                ).dropna()

                if values.empty:
                    continue

                mean_return = float(
                    values.mean()
                )

                win_rate = float(
                    (
                        values > 0.0
                    ).mean()
                )

                mean_mfe = float(
                    mfe_values.mean()
                ) if len(mfe_values) else 0.0

                mean_mae = float(
                    mae_values.mean()
                ) if len(mae_values) else 0.0

                profit_factor = (
                    safe_profit_factor(
                        values
                    )
                )

                risk_adjusted_edge = (
                    mean_return
                    - config.risk_penalty
                    * abs(mean_mae)
                )

                score = (
                    risk_adjusted_edge
                    * row["confidence"]
                )

                prefix = (
                    f"{direction.lower()}_"
                    f"{horizon}"
                )

                row[
                    f"{prefix}_mean_return"
                ] = mean_return

                row[
                    f"{prefix}_win_rate"
                ] = win_rate

                row[
                    f"{prefix}_mean_mfe"
                ] = mean_mfe

                row[
                    f"{prefix}_mean_mae"
                ] = mean_mae

                row[
                    f"{prefix}_profit_factor"
                ] = profit_factor

                row[
                    f"{prefix}_risk_adjusted_edge"
                ] = risk_adjusted_edge

                if (
                    row["eligible"]
                    and score > best_score
                ):
                    best_score = score
                    best_direction = direction
                    best_horizon = int(
                        horizon
                    )
                    best_mean_return = (
                        mean_return
                    )
                    best_win_rate = (
                        win_rate
                    )
                    best_mfe = mean_mfe
                    best_mae = mean_mae
                    best_profit_factor = (
                        profit_factor
                    )

        if (
            not row["eligible"]
            or best_score <= 0.0
        ):
            row[
                "recommended_action"
            ] = (
                "INSUFFICIENT_EVIDENCE"
                if not row["eligible"]
                else "AVOID"
            )

            row[
                "recommended_direction"
            ] = "FLAT"

            row[
                "optimal_horizon_bars"
            ] = 0

            row[
                "trajectory_score"
            ] = 0.0
        else:
            row[
                "recommended_action"
            ] = "ENTER"

            row[
                "recommended_direction"
            ] = best_direction

            row[
                "optimal_horizon_bars"
            ] = best_horizon

            row[
                "trajectory_score"
            ] = float(
                best_score
            )

        row[
            "preferred_mean_return"
        ] = best_mean_return

        row[
            "preferred_win_rate"
        ] = best_win_rate

        row[
            "preferred_mean_mfe"
        ] = best_mfe

        row[
            "preferred_mean_mae"
        ] = best_mae

        row[
            "preferred_profit_factor"
        ] = best_profit_factor

        rows.append(row)

    if not rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "trajectory_score",
                "observation_count",
                "sequence_length",
            ],
            ascending=[
                False,
                False,
                True,
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def build_trajectory_transition_map(
    windows: pd.DataFrame,
) -> pd.DataFrame:
    if windows.empty:
        return pd.DataFrame()

    frame = windows.sort_values(
        [
            "sequence_length",
            "window_end",
        ],
        kind="stable",
    ).copy()

    frame[
        "next_trajectory_id"
    ] = (
        frame.groupby(
            "sequence_length",
            observed=True,
        )[
            "trajectory_id"
        ]
        .shift(-1)
    )

    frame[
        "next_cluster_path"
    ] = (
        frame.groupby(
            "sequence_length",
            observed=True,
        )[
            "cluster_path"
        ]
        .shift(-1)
    )

    frame = frame.dropna(
        subset=[
            "next_trajectory_id",
            "next_cluster_path",
        ]
    )

    result = (
        frame.groupby(
            [
                "sequence_length",
                "trajectory_id",
                "cluster_path",
                "next_trajectory_id",
                "next_cluster_path",
            ],
            sort=True,
            observed=True,
        )
        .size()
        .rename(
            "transition_count"
        )
        .reset_index()
    )

    totals = (
        result.groupby(
            [
                "sequence_length",
                "trajectory_id",
            ]
        )[
            "transition_count"
        ]
        .transform("sum")
    )

    result[
        "transition_probability"
    ] = (
        result[
            "transition_count"
        ]
        / totals
    )

    return (
        result.sort_values(
            [
                "sequence_length",
                "trajectory_id",
                "transition_probability",
            ],
            ascending=[
                True,
                True,
                False,
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def build_latest_trajectory_windows(
    morphology: pd.DataFrame,
    *,
    config: MorphologyTrajectoryConfig,
) -> pd.DataFrame:
    """Construct each latest trajectory directly from the newest bars.

    Research stride is intentionally ignored. Every sequence ends at the
    actual newest available contiguous morphology timestamp.
    """
    source = morphology.copy()

    if config.compress_repeated_states:
        source = compress_consecutive_states(
            source
        )

    segments = split_contiguous_segments(
        source,
        maximum_gap_multiple=(
            config.maximum_gap_multiple
        ),
    )

    if not segments:
        return pd.DataFrame()

    latest_segment = max(
        segments,
        key=lambda frame: frame[
            "timestamp"
        ].max(),
    )

    rows: list[dict[str, Any]] = []

    for sequence_length in (
        config.sequence_lengths
    ):
        if len(latest_segment) < sequence_length:
            continue

        window = latest_segment.tail(
            sequence_length
        )

        cluster_ids = (
            window[
                "morphology_cluster_id"
            ]
            .astype(int)
            .tolist()
        )

        cluster_names = (
            window[
                "morphology_cluster"
            ]
            .astype(str)
            .tolist()
        )

        path = trajectory_key(
            cluster_ids
        )

        rows.append({
            "trajectory_id":
                trajectory_identity(
                    sequence_length=(
                        sequence_length
                    ),
                    cluster_path=path,
                ),
            "sequence_length":
                int(sequence_length),
            "cluster_path":
                path,
            "cluster_name_path":
                "->".join(
                    cluster_names
                ),
            "segment_id":
                -1,
            "window_start":
                window[
                    "timestamp"
                ].iloc[0],
            "window_end":
                window[
                    "timestamp"
                ].iloc[-1],
            "source_cluster_id":
                int(cluster_ids[0]),
            "terminal_cluster_id":
                int(cluster_ids[-1]),
            "source_cluster":
                str(cluster_names[0]),
            "terminal_cluster":
                str(cluster_names[-1]),
            **trajectory_shape_metrics(
                cluster_ids
            ),
        })

    return (
        pd.DataFrame(rows)
        .sort_values(
            "sequence_length",
            kind="stable",
        )
        .reset_index(drop=True)
    )


def recognize_latest_trajectories(
    morphology: pd.DataFrame,
    profiles: pd.DataFrame,
    *,
    config: MorphologyTrajectoryConfig,
) -> pd.DataFrame:
    latest = build_latest_trajectory_windows(
        morphology,
        config=config,
    )

    if latest.empty:
        return pd.DataFrame()

    profile_columns = [
        "trajectory_id",
        "sequence_length",
        "asset",
        "observation_count",
        "eligible",
        "recommended_action",
        "recommended_direction",
        "optimal_horizon_bars",
        "trajectory_score",
        "preferred_mean_return",
        "preferred_win_rate",
        "preferred_mean_mfe",
        "preferred_mean_mae",
        "preferred_profit_factor",
    ]

    available = [
        column
        for column in profile_columns
        if column in profiles.columns
    ]

    return (
        latest.merge(
            profiles[
                available
            ],
            on=[
                "trajectory_id",
                "sequence_length",
            ],
            how="left",
            validate="one_to_many",
        )
        .sort_values(
            [
                "sequence_length",
                "asset",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def write_trajectory_outputs(
    *,
    windows: pd.DataFrame,
    observations: pd.DataFrame,
    profiles: pd.DataFrame,
    transitions: pd.DataFrame,
    latest: pd.DataFrame,
    config: MorphologyTrajectoryConfig,
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
        "windows":
            directory
            / "morphology_trajectory_windows.csv",
        "observations":
            directory
            / "morphology_trajectory_observations.csv",
        "profiles":
            directory
            / "morphology_trajectory_profiles.csv",
        "transitions":
            directory
            / "morphology_trajectory_transitions.csv",
        "latest":
            directory
            / "morphology_latest_trajectories.csv",
        "summary":
            directory
            / "morphology_trajectory_summary.json",
    }

    windows.to_csv(
        outputs["windows"],
        index=False,
    )

    observations.to_csv(
        outputs["observations"],
        index=False,
    )

    profiles.to_csv(
        outputs["profiles"],
        index=False,
    )

    transitions.to_csv(
        outputs["transitions"],
        index=False,
    )

    latest.to_csv(
        outputs["latest"],
        index=False,
    )

    positive = profiles[
        profiles[
            "recommended_action"
        ].eq("ENTER")
    ] if not profiles.empty else pd.DataFrame()

    summary = {
        "schema_version":
            "atlas.morphology_trajectory.v1",
        "config":
            asdict(config),
        "window_count":
            int(len(windows)),
        "observation_count":
            int(len(observations)),
        "profile_count":
            int(len(profiles)),
        "trajectory_transition_count":
            int(len(transitions)),
        "latest_trajectory_rows":
            int(len(latest)),
        "unique_trajectory_count":
            int(
                windows[
                    "trajectory_id"
                ].nunique()
            ) if not windows.empty else 0,
        "positive_trajectory_profiles":
            int(len(positive)),
        "top_trajectories": (
            positive.head(30)
            .replace(
                [np.inf, -np.inf],
                None,
            )
            .to_dict(
                orient="records",
            )
            if not positive.empty
            else []
        ),
    }

    outputs["summary"].write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    return outputs


def run_morphology_trajectory_engine(
    assignments: pd.DataFrame,
    *,
    config: MorphologyTrajectoryConfig = (
        MorphologyTrajectoryConfig()
    ),
) -> dict[str, pd.DataFrame]:
    morphology = build_timestamp_morphology(
        assignments
    )

    windows = extract_trajectory_windows(
        morphology,
        config=config,
    )

    observations = attach_asset_outcomes(
        windows,
        assignments,
        config=config,
    )

    profiles = profile_trajectory_outcomes(
        observations,
        config=config,
    )

    transitions = (
        build_trajectory_transition_map(
            windows
        )
    )

    latest = recognize_latest_trajectories(
        morphology,
        profiles,
        config=config,
    )

    return {
        "morphology":
            morphology,
        "windows":
            windows,
        "observations":
            observations,
        "profiles":
            profiles,
        "transitions":
            transitions,
        "latest":
            latest,
    }
