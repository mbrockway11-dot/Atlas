"""Purged walk-forward validation for morphology trajectories.

Candidate trajectories are evaluated using chronological folds:

1. Discover whether the candidate has positive evidence in training history.
2. Freeze its path, direction, and horizon.
3. Evaluate only later unseen observations.
4. Purge observations whose future outcome horizon crosses a fold boundary.

Research only. No portfolio or execution actions are produced.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from atlas.investment.morphology_intelligence.trajectory import (
    MorphologyTrajectoryConfig,
    attach_asset_outcomes,
    build_timestamp_morphology,
    extract_trajectory_windows,
    infer_bar_interval,
)


DEFAULT_CANDIDATES = (
    {
        "candidate_id": "SOL_LONG_5_7_3_H8",
        "asset": "SOL",
        "cluster_path": "5->7->3",
        "sequence_length": 3,
        "direction": "LONG",
        "horizon_bars": 8,
    },
    {
        "candidate_id": "ETH_LONG_8_8_8_3_8_H32",
        "asset": "ETH",
        "cluster_path": "8->8->8->3->8",
        "sequence_length": 5,
        "direction": "LONG",
        "horizon_bars": 32,
    },
    {
        "candidate_id": "BTC_LONG_3_7_3_H8",
        "asset": "BTC",
        "cluster_path": "3->7->3",
        "sequence_length": 3,
        "direction": "LONG",
        "horizon_bars": 8,
    },
    {
        "candidate_id": "BTC_LONG_8_8_8_3_8_H32",
        "asset": "BTC",
        "cluster_path": "8->8->8->3->8",
        "sequence_length": 5,
        "direction": "LONG",
        "horizon_bars": 32,
    },
)


@dataclass(frozen=True, slots=True)
class TrajectoryWalkForwardConfig:
    fold_count: int = 5
    minimum_training_observations: int = 50
    minimum_test_observations: int = 10
    risk_penalty: float = 0.50
    initial_training_fraction: float = 0.50

    def __post_init__(self) -> None:
        if self.fold_count < 2:
            raise ValueError(
                "fold_count must be at least 2."
            )

        if self.minimum_training_observations < 2:
            raise ValueError(
                "minimum_training_observations must be at least 2."
            )

        if self.minimum_test_observations < 1:
            raise ValueError(
                "minimum_test_observations must be positive."
            )

        if not 0.25 <= self.initial_training_fraction < 0.90:
            raise ValueError(
                "initial_training_fraction must be between 0.25 and 0.90."
            )


def build_walk_forward_boundaries(
    timestamps: pd.Series,
    *,
    config: TrajectoryWalkForwardConfig,
) -> list[dict[str, pd.Timestamp]]:
    ordered = (
        pd.to_datetime(
            timestamps,
            utc=True,
            errors="coerce",
        )
        .dropna()
        .sort_values()
        .drop_duplicates()
        .reset_index(drop=True)
    )

    count = len(ordered)

    if count < config.fold_count + 2:
        raise ValueError(
            "Not enough timestamps for requested folds."
        )

    first_test_index = int(
        count
        * config.initial_training_fraction
    )

    remaining = (
        count - first_test_index
    )

    test_size = max(
        1,
        remaining // config.fold_count,
    )

    folds = []

    for fold_id in range(
        config.fold_count
    ):
        test_start_index = (
            first_test_index
            + fold_id * test_size
        )

        if test_start_index >= count:
            break

        test_end_index = (
            count - 1
            if fold_id
            == config.fold_count - 1
            else min(
                count - 1,
                test_start_index
                + test_size - 1,
            )
        )

        folds.append({
            "fold_id":
                int(fold_id + 1),
            "train_start":
                ordered.iloc[0],
            "test_start":
                ordered.iloc[
                    test_start_index
                ],
            "test_end":
                ordered.iloc[
                    test_end_index
                ],
        })

    return folds


def outcome_columns(
    *,
    direction: str,
    horizon: int,
) -> tuple[str, str, str]:
    if direction == "LONG":
        return (
            f"forward_return_{horizon}",
            f"long_mfe_{horizon}",
            f"long_mae_{horizon}",
        )

    if direction == "SHORT":
        return (
            f"short_return_{horizon}",
            f"short_mfe_{horizon}",
            f"short_mae_{horizon}",
        )

    raise ValueError(
        f"Unsupported direction: {direction}"
    )


def evaluate_outcomes(
    frame: pd.DataFrame,
    *,
    direction: str,
    horizon: int,
    risk_penalty: float,
) -> dict[str, float]:
    return_column, mfe_column, mae_column = (
        outcome_columns(
            direction=direction,
            horizon=horizon,
        )
    )

    values = pd.to_numeric(
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

    if values.empty:
        return {
            "observation_count": 0,
            "mean_return": 0.0,
            "median_return": 0.0,
            "win_rate": 0.0,
            "mean_mfe": 0.0,
            "mean_mae": 0.0,
            "profit_factor": 0.0,
            "risk_adjusted_edge": 0.0,
        }

    gains = values[
        values > 0.0
    ].sum()

    losses = values[
        values < 0.0
    ].abs().sum()

    profit_factor = (
        float(gains / losses)
        if losses > 0.0
        else (
            float("inf")
            if gains > 0.0
            else 0.0
        )
    )

    mean_return = float(
        values.mean()
    )

    mean_mae = float(
        mae.mean()
    ) if len(mae) else 0.0

    return {
        "observation_count":
            int(len(values)),
        "mean_return":
            mean_return,
        "median_return":
            float(values.median()),
        "win_rate":
            float(
                (
                    values > 0.0
                ).mean()
            ),
        "mean_mfe":
            float(
                mfe.mean()
            ) if len(mfe) else 0.0,
        "mean_mae":
            mean_mae,
        "profit_factor":
            profit_factor,
        "risk_adjusted_edge":
            float(
                mean_return
                - risk_penalty
                * abs(mean_mae)
            ),
    }


def select_candidate_rows(
    observations: pd.DataFrame,
    candidate: dict[str, Any],
) -> pd.DataFrame:
    return observations[
        observations[
            "cluster_path"
        ].eq(
            candidate[
                "cluster_path"
            ]
        )
        & observations[
            "sequence_length"
        ].eq(
            int(
                candidate[
                    "sequence_length"
                ]
            )
        )
        & observations[
            "asset"
        ].eq(
            str(
                candidate["asset"]
            )
        )
    ].copy()


def run_trajectory_walk_forward(
    assignments: pd.DataFrame,
    *,
    trajectory_config: MorphologyTrajectoryConfig,
    validation_config: TrajectoryWalkForwardConfig,
    candidates: tuple[dict[str, Any], ...] = (
        DEFAULT_CANDIDATES
    ),
) -> pd.DataFrame:
    morphology = build_timestamp_morphology(
        assignments
    )

    windows = extract_trajectory_windows(
        morphology,
        config=trajectory_config,
    )

    observations = attach_asset_outcomes(
        windows,
        assignments,
        config=trajectory_config,
    )

    interval = infer_bar_interval(
        morphology["timestamp"]
    )

    folds = build_walk_forward_boundaries(
        morphology["timestamp"],
        config=validation_config,
    )

    rows = []

    for candidate in candidates:
        candidate_rows = select_candidate_rows(
            observations,
            candidate,
        )

        horizon = int(
            candidate[
                "horizon_bars"
            ]
        )

        embargo = (
            interval * horizon
        )

        for fold in folds:
            train_label_end = (
                fold["test_start"]
                - embargo
            )

            test_label_end = (
                fold["test_end"]
                - embargo
            )

            training = candidate_rows[
                candidate_rows[
                    "window_end"
                ].lt(
                    train_label_end
                )
            ]

            testing = candidate_rows[
                candidate_rows[
                    "window_end"
                ].ge(
                    fold["test_start"]
                )
                & candidate_rows[
                    "window_end"
                ].le(
                    test_label_end
                )
            ]

            train_metrics = evaluate_outcomes(
                training,
                direction=str(
                    candidate["direction"]
                ),
                horizon=horizon,
                risk_penalty=(
                    validation_config.risk_penalty
                ),
            )

            test_metrics = evaluate_outcomes(
                testing,
                direction=str(
                    candidate["direction"]
                ),
                horizon=horizon,
                risk_penalty=(
                    validation_config.risk_penalty
                ),
            )

            discovered = bool(
                train_metrics[
                    "observation_count"
                ]
                >= validation_config.minimum_training_observations
                and train_metrics[
                    "risk_adjusted_edge"
                ] > 0.0
            )

            test_eligible = bool(
                test_metrics[
                    "observation_count"
                ]
                >= validation_config.minimum_test_observations
            )

            passed = bool(
                discovered
                and test_eligible
                and test_metrics[
                    "risk_adjusted_edge"
                ] > 0.0
                and test_metrics[
                    "mean_return"
                ] > 0.0
            )

            rows.append({
                "candidate_id":
                    candidate[
                        "candidate_id"
                    ],
                "asset":
                    candidate["asset"],
                "cluster_path":
                    candidate[
                        "cluster_path"
                    ],
                "sequence_length":
                    int(
                        candidate[
                            "sequence_length"
                        ]
                    ),
                "direction":
                    candidate[
                        "direction"
                    ],
                "horizon_bars":
                    horizon,
                "fold_id":
                    fold["fold_id"],
                "train_end":
                    train_label_end,
                "test_start":
                    fold["test_start"],
                "test_end":
                    fold["test_end"],
                "embargo_bars":
                    horizon,
                "discovered_in_training":
                    discovered,
                "test_eligible":
                    test_eligible,
                "passed_test":
                    passed,
                **{
                    f"train_{key}": value
                    for key, value
                    in train_metrics.items()
                },
                **{
                    f"test_{key}": value
                    for key, value
                    in test_metrics.items()
                },
            })

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "candidate_id",
                "fold_id",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def summarize_walk_forward(
    folds: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    for candidate_id, group in folds.groupby(
        "candidate_id",
        sort=True,
        observed=True,
    ):
        discovered = group[
            "discovered_in_training"
        ].astype(bool)

        eligible = group[
            "test_eligible"
        ].astype(bool)

        valid = group[
            discovered & eligible
        ]

        passed = valid[
            "passed_test"
        ].astype(bool)

        total_test_observations = int(
            valid[
                "test_observation_count"
            ].sum()
        ) if not valid.empty else 0

        weighted_test_return = (
            float(
                np.average(
                    valid[
                        "test_mean_return"
                    ],
                    weights=valid[
                        "test_observation_count"
                    ],
                )
            )
            if (
                not valid.empty
                and total_test_observations > 0
            )
            else 0.0
        )

        weighted_test_edge = (
            float(
                np.average(
                    valid[
                        "test_risk_adjusted_edge"
                    ],
                    weights=valid[
                        "test_observation_count"
                    ],
                )
            )
            if (
                not valid.empty
                and total_test_observations > 0
            )
            else 0.0
        )

        first = group.iloc[0]

        rows.append({
            "candidate_id":
                candidate_id,
            "asset":
                first["asset"],
            "cluster_path":
                first["cluster_path"],
            "sequence_length":
                int(
                    first[
                        "sequence_length"
                    ]
                ),
            "direction":
                first["direction"],
            "horizon_bars":
                int(
                    first[
                        "horizon_bars"
                    ]
                ),
            "fold_count":
                int(len(group)),
            "discovered_fold_count":
                int(discovered.sum()),
            "eligible_test_fold_count":
                int(eligible.sum()),
            "validated_fold_count":
                int(len(valid)),
            "passed_fold_count":
                int(passed.sum()),
            "fold_pass_rate":
                float(
                    passed.mean()
                ) if len(passed) else 0.0,
            "total_test_observations":
                total_test_observations,
            "weighted_test_mean_return":
                weighted_test_return,
            "weighted_test_risk_adjusted_edge":
                weighted_test_edge,
            "promotion_candidate":
                bool(
                    len(valid) >= 3
                    and passed.mean() >= 0.60
                    and weighted_test_return > 0.0
                    and weighted_test_edge > 0.0
                ),
        })

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "promotion_candidate",
                "fold_pass_rate",
                "weighted_test_risk_adjusted_edge",
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


def write_walk_forward_outputs(
    *,
    folds: pd.DataFrame,
    summary: pd.DataFrame,
    trajectory_config: MorphologyTrajectoryConfig,
    validation_config: TrajectoryWalkForwardConfig,
    output_dir: str | Path,
) -> dict[str, Path]:
    directory = Path(
        output_dir
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    fold_path = (
        directory
        / "trajectory_walk_forward_folds.csv"
    )

    summary_path = (
        directory
        / "trajectory_walk_forward_summary.csv"
    )

    report_path = (
        directory
        / "trajectory_walk_forward_report.json"
    )

    folds.to_csv(
        fold_path,
        index=False,
    )

    summary.to_csv(
        summary_path,
        index=False,
    )

    report = {
        "schema_version":
            "atlas.morphology_trajectory.walk_forward.v1",
        "trajectory_config":
            asdict(
                trajectory_config
            ),
        "validation_config":
            asdict(
                validation_config
            ),
        "candidate_count":
            int(
                summary[
                    "candidate_id"
                ].nunique()
            ),
        "fold_rows":
            int(len(folds)),
        "promotion_candidates":
            summary[
                summary[
                    "promotion_candidate"
                ].astype(bool)
            ].to_dict(
                orient="records"
            ),
        "candidate_summary":
            summary.to_dict(
                orient="records"
            ),
    }

    report_path.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "folds":
            fold_path,
        "summary":
            summary_path,
        "report":
            report_path,
    }
