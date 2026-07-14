"""Build Atlas research observations from LYFE market morphology.

The generator joins synchronized LYFE topology snapshots to asset-level OHLC
history and labels each point-in-time morphology with future price-path
outcomes.

Research only. This module does not generate orders or position sizes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


DEFAULT_HORIZONS = (1, 2, 4, 8, 16, 32, 96)

TOPOLOGY_REQUIRED = {
    "timestamp",
    "rank_state",
    "prior_rank_state",
    "transition",
    "persistence_bars",
    "entropy",
    "leader",
    "laggard",
    "concentration",
    "dispersion",
    "transition_velocity",
    "multi_timeframe_agreement",
    "sol_fulcrum_score",
}

MARKET_REQUIRED = {
    "timestamp",
    "asset",
    "open",
    "high",
    "low",
    "close",
}


@dataclass(frozen=True, slots=True)
class MorphologyObservationConfig:
    horizons: tuple[int, ...] = DEFAULT_HORIZONS
    target_horizon: int = 16
    engine_id: str = "LYFE_MORPHOLOGY_V1"
    entry_model: str = "NEXT_BAR_OPEN"

    def __post_init__(self) -> None:
        horizons = tuple(sorted(set(int(value) for value in self.horizons)))

        if not horizons or any(value < 1 for value in horizons):
            raise ValueError("horizons must contain positive integers.")

        if self.target_horizon not in horizons:
            raise ValueError(
                "target_horizon must be included in horizons."
            )

        if self.entry_model != "NEXT_BAR_OPEN":
            raise ValueError(
                "Only NEXT_BAR_OPEN is supported in v1."
            )


def load_topology(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path, low_memory=False)

    missing = sorted(TOPOLOGY_REQUIRED - set(frame.columns))
    if missing:
        raise ValueError(
            f"Topology input is missing required columns: {missing}"
        )

    frame = frame.copy()
    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        utc=True,
        errors="coerce",
    )

    frame = (
        frame.dropna(subset=["timestamp", "rank_state"])
        .sort_values("timestamp", kind="stable")
        .drop_duplicates(subset=["timestamp"], keep="last")
        .reset_index(drop=True)
    )

    frame["next_rank_state"] = frame["rank_state"].shift(-1)
    frame["next_transition"] = frame["transition"].shift(-1)

    return frame


def load_market_history(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path, low_memory=False)

    rename_map = {}

    if "symbol" in frame.columns and "asset" not in frame.columns:
        rename_map["symbol"] = "asset"

    if "datetime" in frame.columns and "timestamp" not in frame.columns:
        rename_map["datetime"] = "timestamp"

    if rename_map:
        frame = frame.rename(columns=rename_map)

    missing = sorted(MARKET_REQUIRED - set(frame.columns))
    if missing:
        raise ValueError(
            f"Market input is missing required columns: {missing}"
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

    for column in ("open", "high", "low", "close"):
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    frame = (
        frame.dropna(
            subset=[
                "timestamp",
                "asset",
                "open",
                "high",
                "low",
                "close",
            ]
        )
        .sort_values(
            ["asset", "timestamp"],
            kind="stable",
        )
        .drop_duplicates(
            subset=["asset", "timestamp"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    return frame


def future_window_max(series: pd.Series, horizon: int) -> pd.Series:
    """Maximum over bars t+1 through t+horizon."""
    return (
        series.shift(-1)
        .rolling(
            window=horizon,
            min_periods=horizon,
        )
        .max()
        .shift(-(horizon - 1))
    )


def future_window_min(series: pd.Series, horizon: int) -> pd.Series:
    """Minimum over bars t+1 through t+horizon."""
    return (
        series.shift(-1)
        .rolling(
            window=horizon,
            min_periods=horizon,
        )
        .min()
        .shift(-(horizon - 1))
    )


def stable_observation_id(
    *,
    engine_id: str,
    asset: str,
    timestamp: pd.Timestamp,
) -> str:
    payload = (
        f"{engine_id}|{asset}|{timestamp.isoformat()}"
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()[:24]


def label_asset_path(
    asset_frame: pd.DataFrame,
    *,
    config: MorphologyObservationConfig,
) -> pd.DataFrame:
    ordered = (
        asset_frame.sort_values(
            "timestamp",
            kind="stable",
        )
        .reset_index(drop=True)
        .copy()
    )

    ordered["entry_price"] = ordered["open"].shift(-1)
    ordered["entry_timestamp"] = ordered["timestamp"].shift(-1)

    entry = ordered["entry_price"]

    for horizon in config.horizons:
        exit_close = ordered["close"].shift(-horizon)
        future_high = future_window_max(
            ordered["high"],
            horizon,
        )
        future_low = future_window_min(
            ordered["low"],
            horizon,
        )

        ordered[f"exit_close_{horizon}"] = exit_close

        ordered[f"forward_return_{horizon}"] = (
            exit_close / entry - 1.0
        )

        ordered[f"long_mfe_{horizon}"] = (
            future_high / entry - 1.0
        )

        ordered[f"long_mae_{horizon}"] = (
            future_low / entry - 1.0
        )

        ordered[f"short_return_{horizon}"] = (
            entry / exit_close - 1.0
        )

        ordered[f"short_mfe_{horizon}"] = (
            entry / future_low - 1.0
        )

        ordered[f"short_mae_{horizon}"] = (
            entry / future_high - 1.0
        )

        ordered[f"reward_risk_long_{horizon}"] = (
            ordered[f"long_mfe_{horizon}"]
            / ordered[f"long_mae_{horizon}"].abs().replace(0.0, np.nan)
        )

        ordered[f"reward_risk_short_{horizon}"] = (
            ordered[f"short_mfe_{horizon}"]
            / ordered[f"short_mae_{horizon}"].abs().replace(0.0, np.nan)
        )

    return ordered


def build_morphology_observations(
    topology: pd.DataFrame,
    market_history: pd.DataFrame,
    *,
    config: MorphologyObservationConfig = MorphologyObservationConfig(),
) -> pd.DataFrame:
    labelled_assets = []

    for _, asset_frame in market_history.groupby(
        "asset",
        sort=True,
        observed=True,
    ):
        labelled_assets.append(
            label_asset_path(
                asset_frame,
                config=config,
            )
        )

    labelled = pd.concat(
        labelled_assets,
        ignore_index=True,
    )

    topology_columns = [
        "timestamp",
        "rank_state",
        "prior_rank_state",
        "transition",
        "persistence_bars",
        "entropy",
        "leader",
        "laggard",
        "concentration",
        "dispersion",
        "transition_velocity",
        "multi_timeframe_agreement",
        "sol_fulcrum_score",
        "next_rank_state",
        "next_transition",
    ]

    observations = labelled.merge(
        topology[topology_columns],
        on="timestamp",
        how="inner",
        validate="many_to_one",
    )

    observations["engine_id"] = config.engine_id
    observations["observation_source"] = "lyfe_morphology_v1"
    observations["entry_model"] = config.entry_model
    observations["target_horizon"] = config.target_horizon

    target_column = (
        f"forward_return_{config.target_horizon}"
    )

    observations["trade_return"] = observations[target_column]

    observations["trade_id"] = [
        stable_observation_id(
            engine_id=config.engine_id,
            asset=str(asset),
            timestamp=timestamp,
        )
        for asset, timestamp in zip(
            observations["asset"],
            observations["timestamp"],
        )
    ]

    observations["observation_id"] = observations["trade_id"]

    observations = observations.dropna(
        subset=[
            "timestamp",
            "asset",
            "entry_price",
            "trade_return",
            "rank_state",
        ]
    )

    preferred_columns = [
        "observation_id",
        "trade_id",
        "engine_id",
        "timestamp",
        "entry_timestamp",
        "asset",
        "entry_model",
        "target_horizon",
        "entry_price",
        "trade_return",
        "observation_source",
        "rank_state",
        "prior_rank_state",
        "transition",
        "persistence_bars",
        "entropy",
        "leader",
        "laggard",
        "concentration",
        "dispersion",
        "transition_velocity",
        "multi_timeframe_agreement",
        "sol_fulcrum_score",
        "next_rank_state",
        "next_transition",
    ]

    remaining = [
        column
        for column in observations.columns
        if column not in preferred_columns
    ]

    return (
        observations[
            preferred_columns + remaining
        ]
        .sort_values(
            ["timestamp", "asset", "trade_id"],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def write_morphology_observations(
    observations: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    observations.to_csv(
        path,
        index=False,
    )

    return path


def build_from_paths(
    *,
    topology_path: str | Path,
    market_path: str | Path,
    output_path: str | Path,
    horizons: Iterable[int] = DEFAULT_HORIZONS,
    target_horizon: int = 16,
) -> pd.DataFrame:
    config = MorphologyObservationConfig(
        horizons=tuple(int(value) for value in horizons),
        target_horizon=int(target_horizon),
    )

    topology = load_topology(topology_path)
    market = load_market_history(market_path)

    observations = build_morphology_observations(
        topology,
        market,
        config=config,
    )

    write_morphology_observations(
        observations,
        output_path,
    )

    return observations
