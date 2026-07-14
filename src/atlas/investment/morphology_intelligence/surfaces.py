"""Morphology entry and exit surface research.

This module converts point-in-time LYFE morphology observations into
large-sample entry, direction, and holding-horizon surfaces.

Research only:
- no order creation;
- no portfolio sizing;
- no live execution;
- no mutation of the frozen V32 engines.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


DEFAULT_HORIZONS = (1, 2, 4, 8, 16, 32, 96)

BASE_REQUIRED_COLUMNS = {
    "timestamp",
    "asset",
    "rank_state",
    "transition",
    "entropy",
    "transition_velocity",
    "multi_timeframe_agreement",
    "concentration",
    "dispersion",
    "persistence_bars",
}


@dataclass(frozen=True, slots=True)
class MorphologySurfaceConfig:
    horizons: tuple[int, ...] = DEFAULT_HORIZONS
    minimum_observations: int = 100
    risk_penalty: float = 0.50
    confidence_target: int = 1000
    quantile_bins: int = 4

    def __post_init__(self) -> None:
        horizons = tuple(
            sorted(
                set(
                    int(value)
                    for value in self.horizons
                )
            )
        )

        if not horizons:
            raise ValueError(
                "At least one horizon is required."
            )

        if any(value < 1 for value in horizons):
            raise ValueError(
                "Horizons must be positive integers."
            )

        if self.minimum_observations < 2:
            raise ValueError(
                "minimum_observations must be at least 2."
            )

        if (
            not math.isfinite(self.risk_penalty)
            or self.risk_penalty < 0.0
        ):
            raise ValueError(
                "risk_penalty must be finite and nonnegative."
            )

        if self.confidence_target < 1:
            raise ValueError(
                "confidence_target must be positive."
            )

        if self.quantile_bins < 2:
            raise ValueError(
                "quantile_bins must be at least 2."
            )


def load_morphology_observations(
    path: str | Path,
    *,
    horizons: Iterable[int] = DEFAULT_HORIZONS,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    horizons = tuple(
        int(value)
        for value in horizons
    )

    required = set(
        BASE_REQUIRED_COLUMNS
    )

    for horizon in horizons:
        required.update({
            f"forward_return_{horizon}",
            f"long_mfe_{horizon}",
            f"long_mae_{horizon}",
            f"short_return_{horizon}",
            f"short_mfe_{horizon}",
            f"short_mae_{horizon}",
        })

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            "Morphology observations are missing "
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

    numeric_columns = [
        "entropy",
        "transition_velocity",
        "multi_timeframe_agreement",
        "concentration",
        "dispersion",
        "persistence_bars",
    ]

    for horizon in horizons:
        numeric_columns.extend([
            f"forward_return_{horizon}",
            f"long_mfe_{horizon}",
            f"long_mae_{horizon}",
            f"short_return_{horizon}",
            f"short_mfe_{horizon}",
            f"short_mae_{horizon}",
        ])

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
                "rank_state",
                "transition",
            ]
        )
        .sort_values(
            ["timestamp", "asset"],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def _safe_quantile_bins(
    series: pd.Series,
    *,
    bin_count: int,
    prefix: str,
) -> pd.Series:
    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    valid = numeric.dropna()
    unique_count = int(
        valid.nunique()
    )

    effective_bins = min(
        int(bin_count),
        unique_count,
    )

    if effective_bins < 2:
        return pd.Series(
            f"{prefix}_SINGLE",
            index=series.index,
            dtype="string",
        )

    try:
        ranked = numeric.rank(
            method="average",
            pct=True,
        )

        bins = pd.cut(
            ranked,
            bins=np.linspace(
                0.0,
                1.0,
                effective_bins + 1,
            ),
            labels=[
                f"{prefix}_Q{index}"
                for index in range(
                    1,
                    effective_bins + 1,
                )
            ],
            include_lowest=True,
            duplicates="drop",
        )

        return (
            bins.astype("string")
            .fillna("UNKNOWN")
        )

    except ValueError:
        return pd.Series(
            f"{prefix}_SINGLE",
            index=series.index,
            dtype="string",
        )


def build_morphology_bins(
    observations: pd.DataFrame,
    *,
    config: MorphologySurfaceConfig = MorphologySurfaceConfig(),
) -> pd.DataFrame:
    frame = observations.copy()

    frame["entropy_bin"] = _safe_quantile_bins(
        frame["entropy"],
        bin_count=config.quantile_bins,
        prefix="ENTROPY",
    )

    frame["velocity_bin"] = _safe_quantile_bins(
        frame["transition_velocity"],
        bin_count=config.quantile_bins,
        prefix="VELOCITY",
    )

    frame["agreement_bin"] = _safe_quantile_bins(
        frame["multi_timeframe_agreement"],
        bin_count=config.quantile_bins,
        prefix="AGREEMENT",
    )

    frame["concentration_bin"] = _safe_quantile_bins(
        frame["concentration"],
        bin_count=config.quantile_bins,
        prefix="CONCENTRATION",
    )

    frame["persistence_bin"] = _safe_quantile_bins(
        frame["persistence_bars"],
        bin_count=config.quantile_bins,
        prefix="PERSISTENCE",
    )

    return frame


def _surface_statistics(
    group: pd.DataFrame,
    *,
    direction: str,
    horizon: int,
    config: MorphologySurfaceConfig,
) -> dict:
    if direction == "LONG":
        returns = pd.to_numeric(
            group[f"forward_return_{horizon}"],
            errors="coerce",
        )
        mfe = pd.to_numeric(
            group[f"long_mfe_{horizon}"],
            errors="coerce",
        )
        mae = pd.to_numeric(
            group[f"long_mae_{horizon}"],
            errors="coerce",
        )
    else:
        returns = pd.to_numeric(
            group[f"short_return_{horizon}"],
            errors="coerce",
        )
        mfe = pd.to_numeric(
            group[f"short_mfe_{horizon}"],
            errors="coerce",
        )
        mae = pd.to_numeric(
            group[f"short_mae_{horizon}"],
            errors="coerce",
        )

    valid = pd.DataFrame({
        "return": returns,
        "mfe": mfe,
        "mae": mae,
    }).dropna()

    count = int(
        len(valid)
    )

    if count == 0:
        return {
            "observation_count": 0,
            "win_rate": 0.0,
            "mean_return": 0.0,
            "median_return": 0.0,
            "return_std": 0.0,
            "mean_mfe": 0.0,
            "mean_mae": 0.0,
            "profit_factor": 0.0,
            "risk_adjusted_edge": 0.0,
            "confidence": 0.0,
            "eligible": False,
        }

    positive = valid.loc[
        valid["return"] > 0.0,
        "return",
    ]

    negative = valid.loc[
        valid["return"] < 0.0,
        "return",
    ]

    gross_profit = float(
        positive.sum()
    )

    gross_loss = float(
        negative.abs().sum()
    )

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0.0
        else (
            float("inf")
            if gross_profit > 0.0
            else 0.0
        )
    )

    mean_return = float(
        valid["return"].mean()
    )

    mean_mae = float(
        valid["mae"].mean()
    )

    risk_adjusted_edge = (
        mean_return
        - config.risk_penalty
        * abs(mean_mae)
    )

    confidence = min(
        1.0,
        count
        / float(
            config.confidence_target
        ),
    )

    return {
        "observation_count": count,
        "win_rate": float(
            (valid["return"] > 0.0).mean()
        ),
        "mean_return": mean_return,
        "median_return": float(
            valid["return"].median()
        ),
        "return_std": float(
            valid["return"].std(
                ddof=0
            )
        ),
        "mean_mfe": float(
            valid["mfe"].mean()
        ),
        "mean_mae": mean_mae,
        "profit_factor": profit_factor,
        "risk_adjusted_edge": float(
            risk_adjusted_edge
        ),
        "confidence": float(
            confidence
        ),
        "eligible": bool(
            count
            >= config.minimum_observations
        ),
    }


def build_surface_matrix(
    observations: pd.DataFrame,
    *,
    config: MorphologySurfaceConfig = MorphologySurfaceConfig(),
) -> pd.DataFrame:
    frame = build_morphology_bins(
        observations,
        config=config,
    )

    dimensions = [
        "asset",
        "rank_state",
        "transition",
        "entropy_bin",
        "velocity_bin",
        "agreement_bin",
        "concentration_bin",
        "persistence_bin",
    ]

    rows: list[dict] = []

    grouped = frame.groupby(
        dimensions,
        sort=True,
        observed=True,
        dropna=False,
    )

    for keys, group in grouped:
        base = dict(
            zip(
                dimensions,
                keys,
            )
        )

        for direction in (
            "LONG",
            "SHORT",
        ):
            for horizon in config.horizons:
                metrics = _surface_statistics(
                    group,
                    direction=direction,
                    horizon=horizon,
                    config=config,
                )

                rows.append({
                    **base,
                    "direction": direction,
                    "horizon_bars": int(
                        horizon
                    ),
                    **metrics,
                })

    result = pd.DataFrame(
        rows
    )

    if result.empty:
        return result

    result["edge_confidence_score"] = (
        result["risk_adjusted_edge"]
        * result["confidence"]
    )

    result["surface_status"] = np.where(
        result["eligible"],
        np.where(
            result[
                "risk_adjusted_edge"
            ] > 0.0,
            "POSITIVE_EDGE",
            "NON_POSITIVE_EDGE",
        ),
        "INSUFFICIENT_SAMPLE",
    )

    return (
        result.sort_values(
            [
                "asset",
                "rank_state",
                "transition",
                "direction",
                "horizon_bars",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def build_entry_exit_surfaces(
    surface_matrix: pd.DataFrame,
) -> pd.DataFrame:
    if surface_matrix is None or surface_matrix.empty:
        return pd.DataFrame()

    dimensions = [
        "asset",
        "rank_state",
        "transition",
        "entropy_bin",
        "velocity_bin",
        "agreement_bin",
        "concentration_bin",
        "persistence_bin",
    ]

    rows: list[dict] = []

    for keys, group in surface_matrix.groupby(
        dimensions,
        sort=True,
        observed=True,
        dropna=False,
    ):
        base = dict(
            zip(
                dimensions,
                keys,
            )
        )

        eligible = group[
            group["eligible"]
        ].copy()

        if eligible.empty:
            rows.append({
                **base,
                "recommended_action":
                    "INSUFFICIENT_EVIDENCE",
                "recommended_direction":
                    "FLAT",
                "optimal_horizon_bars": 0,
                "observation_count": int(
                    group[
                        "observation_count"
                    ].max()
                ),
                "win_rate": 0.0,
                "mean_return": 0.0,
                "mean_mfe": 0.0,
                "mean_mae": 0.0,
                "risk_adjusted_edge": 0.0,
                "confidence": 0.0,
                "edge_confidence_score": 0.0,
                "exit_reason":
                    "MINIMUM_SAMPLE_NOT_MET",
            })
            continue

        ranked = eligible.sort_values(
            [
                "edge_confidence_score",
                "risk_adjusted_edge",
                "mean_return",
                "observation_count",
                "horizon_bars",
            ],
            ascending=[
                False,
                False,
                False,
                False,
                True,
            ],
            kind="stable",
        )

        best = ranked.iloc[0]

        positive_edge = bool(
            best[
                "risk_adjusted_edge"
            ] > 0.0
        )

        rows.append({
            **base,
            "recommended_action": (
                "ENTER"
                if positive_edge
                else "AVOID"
            ),
            "recommended_direction": (
                str(
                    best["direction"]
                )
                if positive_edge
                else "FLAT"
            ),
            "optimal_horizon_bars": int(
                best["horizon_bars"]
            ),
            "observation_count": int(
                best["observation_count"]
            ),
            "win_rate": float(
                best["win_rate"]
            ),
            "mean_return": float(
                best["mean_return"]
            ),
            "median_return": float(
                best["median_return"]
            ),
            "return_std": float(
                best["return_std"]
            ),
            "mean_mfe": float(
                best["mean_mfe"]
            ),
            "mean_mae": float(
                best["mean_mae"]
            ),
            "profit_factor": float(
                best["profit_factor"]
            ),
            "risk_adjusted_edge": float(
                best[
                    "risk_adjusted_edge"
                ]
            ),
            "confidence": float(
                best["confidence"]
            ),
            "edge_confidence_score": float(
                best[
                    "edge_confidence_score"
                ]
            ),
            "exit_reason": (
                "OPTIMAL_FORWARD_HORIZON"
                if positive_edge
                else "NO_POSITIVE_EDGE"
            ),
        })

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "edge_confidence_score",
                "observation_count",
            ],
            ascending=[
                False,
                False,
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def write_surface_outputs(
    *,
    surface_matrix: pd.DataFrame,
    entry_exit_surfaces: pd.DataFrame,
    output_dir: str | Path,
    config: MorphologySurfaceConfig,
) -> dict[str, Path]:
    directory = Path(
        output_dir
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    matrix_path = (
        directory
        / "morphology_surface_matrix.csv"
    )

    entry_exit_path = (
        directory
        / "morphology_entry_exit_surfaces.csv"
    )

    summary_path = (
        directory
        / "morphology_surface_summary.json"
    )

    surface_matrix.to_csv(
        matrix_path,
        index=False,
    )

    entry_exit_surfaces.to_csv(
        entry_exit_path,
        index=False,
    )

    positive = entry_exit_surfaces[
        entry_exit_surfaces[
            "recommended_action"
        ].eq("ENTER")
    ]

    summary = {
        "schema_version":
            "atlas.morphology_surfaces.v2",
        "config": asdict(config),
        "surface_matrix_rows": int(
            len(surface_matrix)
        ),
        "entry_exit_surface_rows": int(
            len(entry_exit_surfaces)
        ),
        "positive_entry_surfaces": int(
            len(positive)
        ),
        "assets": sorted(
            entry_exit_surfaces[
                "asset"
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        ),
        "top_surfaces": (
            positive.head(25)
            .replace(
                [np.inf, -np.inf],
                None,
            )
            .to_dict(
                orient="records"
            )
        ),
    }

    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "surface_matrix":
            matrix_path,
        "entry_exit_surfaces":
            entry_exit_path,
        "summary":
            summary_path,
    }
