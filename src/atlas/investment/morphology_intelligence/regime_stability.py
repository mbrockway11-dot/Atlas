"""Morphology Regime Stability Validation V1.

Evaluates previously discovered morphology expressions inside independently
constructed, past-only market regimes.

Regimes:
- trend: BULL, BEAR, NEUTRAL
- volatility: HIGH_VOL, LOW_VOL
- liquidity: EXPANDING_LIQUIDITY, CONTRACTING_LIQUIDITY

The validator preserves:
- chronological folds;
- cluster-matched controls;
- non-overlapping outcomes;
- transaction costs;
- discovery/validation separation;
- multiple-testing correction.

Research only. No portfolio intents or execution actions are produced.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from atlas.investment.morphology_intelligence.discovery import (
    exact_sign_test_p_value,
    matched_non_overlapping_samples,
)
from atlas.investment.morphology_intelligence.expression_v3 import (
    apply_expression_candidate,
)
from atlas.investment.morphology_intelligence.field_incremental_value import (
    FieldIncrementalValueConfig,
    benjamini_hochberg,
    cluster_weighted_uplift,
    load_incremental_outcomes,
    sample_metrics,
)


@dataclass(frozen=True, slots=True)
class MorphologyRegimeStabilityConfig:
    horizon_bars: int = 16
    transaction_cost_bps: float = 8.0
    non_overlap_bars: int = 16

    trend_lookback_bars: int = 384
    volatility_lookback_bars: int = 96
    liquidity_lookback_bars: int = 96
    regime_reference_asset: str = "BTC"

    bull_threshold: float = 0.03
    bear_threshold: float = -0.03
    liquidity_expansion_threshold: float = 1.05

    minimum_condition_observations: int = 8
    minimum_control_observations: int = 8
    minimum_cluster_observations: int = 16
    minimum_regime_folds: int = 4
    minimum_positive_uplift_rate: float = 0.60
    multiple_testing_alpha: float = 0.10

    def __post_init__(self) -> None:
        for name in (
            "horizon_bars",
            "non_overlap_bars",
            "trend_lookback_bars",
            "volatility_lookback_bars",
            "liquidity_lookback_bars",
            "minimum_condition_observations",
            "minimum_control_observations",
            "minimum_cluster_observations",
            "minimum_regime_folds",
        ):
            if int(getattr(self, name)) < 1:
                raise ValueError(
                    f"{name} must be positive."
                )

        if self.transaction_cost_bps < 0.0:
            raise ValueError(
                "transaction_cost_bps cannot be negative."
            )

        if not 0.0 < self.minimum_positive_uplift_rate <= 1.0:
            raise ValueError(
                "minimum_positive_uplift_rate must be in (0, 1]."
            )

        if not 0.0 < self.multiple_testing_alpha < 1.0:
            raise ValueError(
                "multiple_testing_alpha must be between zero and one."
            )


def load_regime_features(
    path: str | Path,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "timestamp",
        "fold_id",
        "asset",
        "morphology_cluster_id",
        "field_supported",
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            f"Expression features missing columns: {missing}"
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

    frame["asset"] = (
        frame["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    return (
        frame.dropna(
            subset=[
                "timestamp",
                "fold_id",
                "morphology_cluster_id",
            ]
        )
        .assign(
            fold_id=lambda value:
                value["fold_id"].astype(int),
            morphology_cluster_id=lambda value:
                value["morphology_cluster_id"].astype(int),
        )
        .sort_values(
            [
                "fold_id",
                "timestamp",
                "asset",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def load_regime_catalog(
    path: str | Path,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "candidate_id",
        "candidate_kind",
        "expression",
        "feature_a",
        "operator_a",
        "value_a",
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            f"Expression catalog missing columns: {missing}"
        )

    return frame.fillna("").reset_index(
        drop=True
    )


def load_expression_summary(
    path: str | Path,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    if frame.empty:
        return frame

    required = {
        "candidate_id",
        "asset",
        "direction",
        "discovered",
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            f"Expression summary missing columns: {missing}"
        )

    frame["asset"] = (
        frame["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    frame["direction"] = (
        frame["direction"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    frame["discovered"] = (
        frame["discovered"]
        .astype(str)
        .str.lower()
        .isin({"true", "1", "yes"})
    )

    return frame.reset_index(drop=True)


def load_regime_market(
    path: str | Path,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "timestamp",
        "asset",
        "close",
        "volume",
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            f"Market file missing columns: {missing}"
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

    frame["close"] = pd.to_numeric(
        frame["close"],
        errors="coerce",
    )

    frame["volume"] = pd.to_numeric(
        frame["volume"],
        errors="coerce",
    )

    return (
        frame.dropna(
            subset=[
                "timestamp",
                "asset",
                "close",
            ]
        )
        .sort_values(
            [
                "asset",
                "timestamp",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def build_past_only_regimes(
    market: pd.DataFrame,
    *,
    config: MorphologyRegimeStabilityConfig,
) -> pd.DataFrame:
    reference = market[
        market["asset"].eq(
            config.regime_reference_asset.upper()
        )
    ].copy()

    if reference.empty:
        raise ValueError(
            "Reference asset is absent from market data: "
            f"{config.regime_reference_asset}"
        )

    reference = (
        reference.sort_values(
            "timestamp",
            kind="stable",
        )
        .drop_duplicates(
            subset=["timestamp"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    close = reference["close"]
    returns = close.pct_change()

    reference["regime_trend_return"] = (
        close
        / close.shift(
            config.trend_lookback_bars
        )
        - 1.0
    )

    reference["regime_realized_volatility"] = (
        returns.rolling(
            config.volatility_lookback_bars,
            min_periods=(
                config.volatility_lookback_bars
            ),
        )
        .std()
        * math.sqrt(
            config.volatility_lookback_bars
        )
    )

    # Expanding median uses only prior observations.
    reference["regime_volatility_median"] = (
        reference[
            "regime_realized_volatility"
        ]
        .shift(1)
        .expanding(
            min_periods=(
                config.volatility_lookback_bars
            )
        )
        .median()
    )

    rolling_volume = (
        reference["volume"]
        .rolling(
            config.liquidity_lookback_bars,
            min_periods=(
                config.liquidity_lookback_bars
            ),
        )
        .mean()
    )

    prior_volume = rolling_volume.shift(
        config.liquidity_lookback_bars
    )

    reference["regime_liquidity_ratio"] = (
        rolling_volume
        / prior_volume.replace(
            0.0,
            np.nan,
        )
    )

    trend_return = reference[
        "regime_trend_return"
    ]

    reference["trend_regime"] = np.select(
        [
            trend_return.ge(
                config.bull_threshold
            ),
            trend_return.le(
                config.bear_threshold
            ),
        ],
        [
            "BULL",
            "BEAR",
        ],
        default="NEUTRAL",
    )

    reference["volatility_regime"] = np.where(
        reference[
            "regime_realized_volatility"
        ].ge(
            reference[
                "regime_volatility_median"
            ]
        ),
        "HIGH_VOL",
        "LOW_VOL",
    )

    reference["liquidity_regime"] = np.where(
        reference[
            "regime_liquidity_ratio"
        ].ge(
            config.liquidity_expansion_threshold
        ),
        "EXPANDING_LIQUIDITY",
        "CONTRACTING_LIQUIDITY",
    )

    reference["combined_regime"] = (
        reference["trend_regime"]
        + "|"
        + reference["volatility_regime"]
        + "|"
        + reference["liquidity_regime"]
    )

    valid = reference[
        [
            "regime_trend_return",
            "regime_realized_volatility",
            "regime_volatility_median",
            "regime_liquidity_ratio",
        ]
    ].notna().all(axis=1)

    return (
        reference.loc[
            valid,
            [
                "timestamp",
                "trend_regime",
                "volatility_regime",
                "liquidity_regime",
                "combined_regime",
                "regime_trend_return",
                "regime_realized_volatility",
                "regime_liquidity_ratio",
            ],
        ]
        .reset_index(drop=True)
    )


def incremental_config(
    config: MorphologyRegimeStabilityConfig,
) -> FieldIncrementalValueConfig:
    return FieldIncrementalValueConfig(
        horizon_bars=config.horizon_bars,
        transaction_cost_bps=(
            config.transaction_cost_bps
        ),
        non_overlap_bars=(
            config.non_overlap_bars
        ),
        minimum_condition_observations=(
            config.minimum_condition_observations
        ),
        minimum_control_observations=(
            config.minimum_control_observations
        ),
        minimum_cluster_observations=(
            config.minimum_cluster_observations
        ),
        minimum_valid_folds=(
            config.minimum_regime_folds
        ),
        bootstrap_iterations=10,
        permutation_iterations=10,
    )


def evaluate_regime_fold(
    frame: pd.DataFrame,
    *,
    candidate: dict[str, Any],
    direction: str,
    config: MorphologyRegimeStabilityConfig,
) -> dict[str, Any] | None:
    mask = apply_expression_candidate(
        frame,
        candidate,
    )

    discovery_config = config_for_matching(
        config
    )

    condition, control = (
        matched_non_overlapping_samples(
            frame,
            candidate_mask=mask,
            config=discovery_config,
        )
    )

    if (
        len(condition)
        < config.minimum_condition_observations
        or len(control)
        < config.minimum_control_observations
    ):
        return None

    value_config = incremental_config(
        config
    )

    uplift, details = cluster_weighted_uplift(
        condition,
        control,
        direction=direction,
        config=value_config,
    )

    if details.empty:
        return None

    condition_metrics = sample_metrics(
        condition,
        direction=direction,
        config=value_config,
    )

    control_metrics = sample_metrics(
        control,
        direction=direction,
        config=value_config,
    )

    return {
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
            int(len(details)),
        "condition_net_mean_return":
            float(
                condition_metrics[
                    "net_mean_return"
                ]
            ),
        "control_net_mean_return":
            float(
                control_metrics[
                    "net_mean_return"
                ]
            ),
        "cluster_matched_uplift":
            float(uplift),
        "condition_net_win_rate":
            float(
                condition_metrics[
                    "net_win_rate"
                ]
            ),
        "control_net_win_rate":
            float(
                control_metrics[
                    "net_win_rate"
                ]
            ),
        "condition_profit_factor":
            float(
                condition_metrics[
                    "profit_factor"
                ]
            ),
    }


def config_for_matching(
    config: MorphologyRegimeStabilityConfig,
):
    from atlas.investment.morphology_intelligence.discovery import (
        MorphologyDiscoveryConfig,
    )

    return MorphologyDiscoveryConfig(
        horizon_bars=config.horizon_bars,
        transaction_cost_bps=(
            config.transaction_cost_bps
        ),
        non_overlap_bars=(
            config.non_overlap_bars
        ),
        minimum_raw_candidate_rows=1,
        minimum_condition_observations=(
            config.minimum_condition_observations
        ),
        minimum_control_observations=(
            config.minimum_control_observations
        ),
        minimum_cluster_observations=(
            config.minimum_cluster_observations
        ),
        minimum_discovery_folds=1,
        minimum_validation_folds=1,
    )


def run_regime_stability_validation(
    *,
    features: pd.DataFrame,
    outcomes: pd.DataFrame,
    regimes: pd.DataFrame,
    catalog: pd.DataFrame,
    expression_summary: pd.DataFrame,
    config: MorphologyRegimeStabilityConfig,
) -> pd.DataFrame:
    discovered = expression_summary[
        expression_summary[
            "discovered"
        ].astype(bool)
    ].copy()

    if discovered.empty:
        return pd.DataFrame()

    catalog_map = {
        str(row["candidate_id"]):
            row
        for row in catalog.to_dict(
            orient="records"
        )
    }

    joined = outcomes.merge(
        features,
        on=[
            "timestamp",
            "asset",
            "morphology_cluster_id",
        ],
        how="inner",
        validate="many_to_one",
        suffixes=(
            "",
            "_expression",
        ),
    )

    joined = joined.merge(
        regimes,
        on="timestamp",
        how="inner",
        validate="many_to_one",
    )

    rows: list[dict[str, Any]] = []

    for discovered_row in discovered.to_dict(
        orient="records"
    ):
        candidate_id = str(
            discovered_row[
                "candidate_id"
            ]
        )

        candidate = catalog_map.get(
            candidate_id
        )

        if candidate is None:
            continue

        asset = str(
            discovered_row[
                "asset"
            ]
        ).upper()

        direction = str(
            discovered_row[
                "direction"
            ]
        ).upper()

        asset_frame = joined[
            joined["asset"].eq(asset)
        ]

        for regime_dimension in (
            "trend_regime",
            "volatility_regime",
            "liquidity_regime",
            "combined_regime",
        ):
            for regime_value, regime_frame in (
                asset_frame.groupby(
                    regime_dimension,
                    sort=True,
                    observed=True,
                )
            ):
                for fold_id, fold_frame in (
                    regime_frame.groupby(
                        "fold_id",
                        sort=True,
                        observed=True,
                    )
                ):
                    result = evaluate_regime_fold(
                        fold_frame,
                        candidate=candidate,
                        direction=direction,
                        config=config,
                    )

                    if result is None:
                        continue

                    rows.append({
                        "candidate_id":
                            candidate_id,
                        "candidate_kind":
                            candidate.get(
                                "candidate_kind",
                                "",
                            ),
                        "expression":
                            candidate.get(
                                "expression",
                                "",
                            ),
                        "asset":
                            asset,
                        "direction":
                            direction,
                        "regime_dimension":
                            regime_dimension,
                        "regime_value":
                            str(regime_value),
                        "fold_id":
                            int(fold_id),
                        **result,
                    })

    if not rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "candidate_id",
                "asset",
                "direction",
                "regime_dimension",
                "regime_value",
                "fold_id",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def summarize_regime_stability(
    evaluations: pd.DataFrame,
    *,
    config: MorphologyRegimeStabilityConfig,
) -> pd.DataFrame:
    if evaluations.empty:
        return pd.DataFrame()

    rows = []

    dimensions = [
        "candidate_id",
        "candidate_kind",
        "expression",
        "asset",
        "direction",
        "regime_dimension",
        "regime_value",
    ]

    for keys, group in evaluations.groupby(
        dimensions,
        sort=True,
        observed=True,
    ):
        weights = group[
            "condition_observations"
        ].clip(lower=1)

        positive_count = int(
            group[
                "cluster_matched_uplift"
            ].gt(0.0).sum()
        )

        fold_count = int(
            len(group)
        )

        rows.append({
            **dict(
                zip(
                    dimensions,
                    keys,
                )
            ),
            "valid_fold_count":
                fold_count,
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
                float(
                    np.average(
                        group[
                            "condition_net_mean_return"
                        ],
                        weights=weights,
                    )
                ),
            "weighted_cluster_matched_uplift":
                float(
                    np.average(
                        group[
                            "cluster_matched_uplift"
                        ],
                        weights=weights,
                    )
                ),
            "weighted_condition_win_rate":
                float(
                    np.average(
                        group[
                            "condition_net_win_rate"
                        ],
                        weights=weights,
                    )
                ),
            "positive_uplift_fold_count":
                positive_count,
            "positive_uplift_fold_rate":
                (
                    positive_count
                    / fold_count
                ),
            "sign_test_p_value":
                exact_sign_test_p_value(
                    positive_count,
                    fold_count,
                ),
        })

    summary = pd.DataFrame(rows)

    summary[
        "bh_adjusted_p_value"
    ] = benjamini_hochberg(
        summary[
            "sign_test_p_value"
        ]
    )

    summary[
        "regime_stable"
    ] = (
        summary[
            "valid_fold_count"
        ].ge(
            config.minimum_regime_folds
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
            "bh_adjusted_p_value"
        ].le(
            config.multiple_testing_alpha
        )
    )

    return (
        summary.sort_values(
            [
                "regime_stable",
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


def build_expression_stability_matrix(
    summary: pd.DataFrame,
) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()

    rows = []

    for keys, group in summary.groupby(
        [
            "candidate_id",
            "expression",
            "asset",
            "direction",
        ],
        sort=True,
        observed=True,
    ):
        (
            candidate_id,
            expression,
            asset,
            direction,
        ) = keys

        positive_regimes = group[
            group[
                "weighted_cluster_matched_uplift"
            ].gt(0.0)
            & group[
                "weighted_condition_net_return"
            ].gt(0.0)
        ]

        stable_regimes = group[
            group[
                "regime_stable"
            ].astype(bool)
        ]

        rows.append({
            "candidate_id":
                candidate_id,
            "expression":
                expression,
            "asset":
                asset,
            "direction":
                direction,
            "tested_regime_count":
                int(len(group)),
            "positive_regime_count":
                int(
                    len(
                        positive_regimes
                    )
                ),
            "stable_regime_count":
                int(
                    len(
                        stable_regimes
                    )
                ),
            "best_regime_dimension":
                (
                    str(
                        group.iloc[0][
                            "regime_dimension"
                        ]
                    )
                ),
            "best_regime_value":
                (
                    str(
                        group.iloc[0][
                            "regime_value"
                        ]
                    )
                ),
            "best_regime_uplift":
                float(
                    group[
                        "weighted_cluster_matched_uplift"
                    ].max()
                ),
            "best_regime_net_return":
                float(
                    group.loc[
                        group[
                            "weighted_cluster_matched_uplift"
                        ].idxmax(),
                        "weighted_condition_net_return",
                    ]
                ),
            "regime_dependent_candidate":
                bool(
                    len(stable_regimes)
                    > 0
                ),
        })

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "regime_dependent_candidate",
                "best_regime_uplift",
            ],
            ascending=[
                False,
                False,
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def write_regime_stability_outputs(
    *,
    regimes: pd.DataFrame,
    evaluations: pd.DataFrame,
    summary: pd.DataFrame,
    stability_matrix: pd.DataFrame,
    config: MorphologyRegimeStabilityConfig,
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
        "regimes":
            directory
            / "morphology_market_regimes.csv",
        "folds":
            directory
            / "morphology_regime_stability_folds.csv",
        "summary":
            directory
            / "morphology_regime_stability_summary.csv",
        "matrix":
            directory
            / "morphology_expression_stability_matrix.csv",
        "validated":
            directory
            / "morphology_regime_stable_expressions.csv",
        "report":
            directory
            / "morphology_regime_stability_report.json",
    }

    regimes.to_csv(
        outputs["regimes"],
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

    stability_matrix.to_csv(
        outputs["matrix"],
        index=False,
    )

    stable = (
        summary[
            summary[
                "regime_stable"
            ].astype(bool)
        ]
        if not summary.empty
        else pd.DataFrame()
    )

    stable.to_csv(
        outputs["validated"],
        index=False,
    )

    report = {
        "schema_version":
            "atlas.morphology_regime_stability.v1",
        "config":
            asdict(config),
        "regime_rows":
            int(len(regimes)),
        "evaluation_rows":
            int(len(evaluations)),
        "summary_rows":
            int(len(summary)),
        "stable_regime_expression_count":
            int(len(stable)),
        "regime_dependent_candidate_count":
            int(
                stability_matrix[
                    "regime_dependent_candidate"
                ].astype(bool).sum()
            ) if not stability_matrix.empty else 0,
        "stable_regime_expressions":
            (
                stable.to_dict(
                    orient="records"
                )
                if not stable.empty
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
