"""Research Experiment Execution source loading."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.common.io import safe_read_csv, safe_read_json
from atlas.investment.artifacts import artifact_path, load_csv, load_json
from atlas.investment.research_experiment_execution.config import (
    ENGINE_COLUMN_CANDIDATES,
    HISTORICAL_FEATURES_PATH,
    HISTORICAL_TRADES_PATH,
    OBSERVATION_SEARCH_PATHS,
    RETURN_COLUMN_CANDIDATES,
    TIMESTAMP_COLUMN_CANDIDATES,
    TRADE_ID_COLUMN_CANDIDATES,
)


SOURCE_KEYS = {
    "program_registry": "research_program_registry",
    "designs": "research_experiment_designs",
    "variants": "research_experiment_variants",
    "fold_plan": "research_experiment_walk_forward_plan",
    "acceptance_criteria": "research_experiment_acceptance_criteria",
    "design_validation": "research_experiment_design_validation",
    "compiler_report": "atlas_compiler_report",
}

SOURCE_PATHS = {
    name: artifact_path(key)
    for name, key in SOURCE_KEYS.items()
}


def load_execution_sources() -> dict[str, Any]:
    sources = {
        name: (
            load_json(key)
            if artifact_path(key).suffix.lower() == ".json"
            else load_csv(key)
        )
        for name, key in SOURCE_KEYS.items()
    }

    observations, observation_path = discover_observations()
    sources["observations"] = observations
    sources["observation_source_path"] = (
        str(observation_path) if observation_path else ""
    )
    return sources


def discover_observations() -> tuple[pd.DataFrame, Path | None]:
    override_value = os.environ.get(
        "ATLAS_RESEARCH_OBSERVATIONS_PATH",
        "",
    ).strip()

    if override_value:
        override_path = Path(override_value)
        override_frame = safe_read_csv(
            override_path
        )

        if not override_frame.empty:
            normalized = normalize_observations(
                override_frame
            )

            if not normalized.empty:
                return normalized, override_path

    historical = build_historical_trade_observations()
    if not historical.empty:
        return historical, HISTORICAL_TRADES_PATH

    for path in OBSERVATION_SEARCH_PATHS:
        if path == HISTORICAL_TRADES_PATH:
            continue
        frame = safe_read_csv(path)
        if frame.empty:
            continue
        normalized = normalize_observations(frame)
        if not normalized.empty:
            return normalized, path
    return pd.DataFrame(), None


def build_historical_trade_observations() -> pd.DataFrame:
    trades = safe_read_csv(HISTORICAL_TRADES_PATH)
    features = safe_read_csv(HISTORICAL_FEATURES_PATH)
    if trades.empty or features.empty:
        return pd.DataFrame()

    required_trade_columns = {
        "engine_id",
        "timestamp",
        "asset",
        "strategy_return",
    }
    required_feature_columns = {"timestamp", "asset"}
    if not required_trade_columns.issubset(trades.columns):
        return pd.DataFrame()
    if not required_feature_columns.issubset(features.columns):
        return pd.DataFrame()

    trades = trades.copy()
    features = features.copy()
    trades["timestamp"] = pd.to_datetime(
        trades["timestamp"], utc=True, errors="coerce"
    )
    features["timestamp"] = pd.to_datetime(
        features["timestamp"], utc=True, errors="coerce"
    )
    trades["asset"] = trades["asset"].astype(str)
    features["asset"] = features["asset"].astype(str)
    trades["strategy_return"] = pd.to_numeric(
        trades["strategy_return"], errors="coerce"
    )
    trades = trades.dropna(
        subset=["engine_id", "timestamp", "asset", "strategy_return"]
    )
    features = features.dropna(subset=["timestamp", "asset"])

    feature_columns = [
        column
        for column in features.columns
        if column not in {"open", "high", "low", "close", "volume"}
    ]
    observations = trades.merge(
        features[feature_columns],
        on=["timestamp", "asset"],
        how="left",
        validate="many_to_one",
        suffixes=("", "_feature"),
    )
    observations["trade_return"] = observations["strategy_return"]
    observations["trade_id"] = [
        f"{engine_id}|{asset}|{timestamp.isoformat()}|{index}"
        for index, (engine_id, asset, timestamp) in enumerate(
            zip(
                observations["engine_id"].astype(str),
                observations["asset"].astype(str),
                observations["timestamp"],
            )
        )
    ]
    observations["observation_source"] = (
        "historical_alpha_engine_non_overlapping_trades"
    )
    return observations.sort_values(
        ["engine_id", "asset", "timestamp", "trade_id"],
        kind="stable",
    ).reset_index(drop=True)


def normalize_observations(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()

    engine_column = first_existing_column(frame, ENGINE_COLUMN_CANDIDATES)
    timestamp_column = first_existing_column(frame, TIMESTAMP_COLUMN_CANDIDATES)
    return_column = first_existing_column(frame, RETURN_COLUMN_CANDIDATES)
    if not engine_column or not timestamp_column or not return_column:
        return pd.DataFrame()

    result = frame.copy()
    trade_id_column = first_existing_column(result, TRADE_ID_COLUMN_CANDIDATES)
    rename_map = {
        engine_column: "engine_id",
        timestamp_column: "timestamp",
        return_column: "trade_return",
    }
    if trade_id_column:
        rename_map[trade_id_column] = "trade_id"
    result = result.rename(columns=rename_map)
    result["timestamp"] = pd.to_datetime(
        result["timestamp"], utc=True, errors="coerce"
    )
    result["trade_return"] = pd.to_numeric(
        result["trade_return"], errors="coerce"
    )
    result = result.dropna(
        subset=["engine_id", "timestamp", "trade_return"]
    ).copy()
    if "trade_id" not in result.columns:
        result["trade_id"] = [
            f"OBS-{index:08d}" for index in range(len(result))
        ]
    result["engine_id"] = result["engine_id"].astype(str)
    result["trade_id"] = result["trade_id"].astype(str)
    return result.sort_values(
        ["engine_id", "timestamp", "trade_id"],
        kind="stable",
    ).reset_index(drop=True)


def first_existing_column(
    frame: pd.DataFrame,
    candidates: tuple[str, ...],
) -> str:
    for candidate in candidates:
        if candidate in frame.columns:
            return candidate
    return ""


__all__ = [
    "SOURCE_KEYS",
    "SOURCE_PATHS",
    "build_historical_trade_observations",
    "discover_observations",
    "first_existing_column",
    "load_execution_sources",
    "normalize_observations",
    "safe_read_csv",
    "safe_read_json",
]
