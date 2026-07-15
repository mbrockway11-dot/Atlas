"""V32-Morphology Ensemble Outcome Validator V1.

Pairs historical V32 entry and exit events, attaches morphology ensemble
classifications, prices trades from historical market data, and compares:

- baseline V32;
- retained V32 trades at equal exposure;
- vetoed trades;
- supportive, neutral, and adverse morphology cohorts;
- actual exposure-adjusted ensemble.

Research only. This module does not authorize or submit orders.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ENTER_LONG = "ENTER_LONG"
ENTER_SHORT = "ENTER_SHORT"
EXIT_POSITION = "EXIT_POSITION"

LONG = "LONG"
SHORT = "SHORT"

SUPPORTIVE = "SUPPORTIVE"
NEUTRAL = "NEUTRAL"
ADVERSE = "ADVERSE"


@dataclass(frozen=True, slots=True)
class EnsembleOutcomeConfig:
    transaction_cost_bps: float = 8.0
    baseline_exposure: float = 1.0
    maximum_price_age_bars: int = 2
    bar_minutes: int = 15
    research_only: bool = True

    def __post_init__(self) -> None:
        if self.transaction_cost_bps < 0.0:
            raise ValueError(
                "transaction_cost_bps cannot be negative."
            )

        if self.baseline_exposure <= 0.0:
            raise ValueError(
                "baseline_exposure must be positive."
            )

        if self.maximum_price_age_bars < 0:
            raise ValueError(
                "maximum_price_age_bars cannot be negative."
            )

        if self.bar_minutes < 1:
            raise ValueError(
                "bar_minutes must be positive."
            )

    @property
    def transaction_cost(self) -> float:
        return self.transaction_cost_bps / 10_000.0

    @property
    def price_tolerance(self) -> pd.Timedelta:
        return pd.Timedelta(
            minutes=(
                self.maximum_price_age_bars
                * self.bar_minutes
            )
        )


def _number(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default

    if not math.isfinite(result):
        return default

    return result


def _boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {
        "true",
        "1",
        "yes",
        "y",
    }


def _normalize_action(value: Any) -> str:
    action = str(
        value or ""
    ).strip().upper()

    aliases = {
        "BUY": ENTER_LONG,
        "LONG": ENTER_LONG,
        "SELL_SHORT": ENTER_SHORT,
        "SHORT": ENTER_SHORT,
        "EXIT": EXIT_POSITION,
        "CLOSE": EXIT_POSITION,
    }

    return aliases.get(
        action,
        action,
    )


def _normalize_direction(value: Any) -> str:
    direction = str(
        value or ""
    ).strip().upper()

    if direction not in {
        LONG,
        SHORT,
    }:
        return ""

    return direction


def load_outcome_v32_stream(
    path: str | Path,
) -> pd.DataFrame:
    source = Path(path)

    if not source.exists():
        raise FileNotFoundError(
            f"V32 decision stream does not exist: {source}"
        )

    frame = pd.read_csv(
        source,
        low_memory=False,
    )

    timestamp_column = next(
        (
            column
            for column in (
                "timestamp",
                "decision_timestamp",
                "entry_time",
            )
            if column in frame.columns
        ),
        None,
    )

    if timestamp_column is None:
        raise ValueError(
            "V32 stream requires a timestamp column."
        )

    action_column = next(
        (
            column
            for column in (
                "combined_action",
                "action",
            )
            if column in frame.columns
        ),
        None,
    )

    direction_column = next(
        (
            column
            for column in (
                "combined_direction",
                "direction",
            )
            if column in frame.columns
        ),
        None,
    )

    if action_column is None:
        raise ValueError(
            "V32 stream requires an action column."
        )

    if timestamp_column != "timestamp":
        frame = frame.rename(
            columns={
                timestamp_column: "timestamp",
            }
        )

    result = frame.copy()

    result["timestamp"] = pd.to_datetime(
        result["timestamp"],
        utc=True,
        errors="coerce",
    )

    if "asset" not in result.columns:
        result["asset"] = "SOL"

    result["asset"] = (
        result["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    result["v32_action"] = result[
        action_column
    ].map(_normalize_action)

    if direction_column is None:
        result["v32_direction"] = np.where(
            result["v32_action"].eq(
                ENTER_LONG
            ),
            LONG,
            np.where(
                result["v32_action"].eq(
                    ENTER_SHORT
                ),
                SHORT,
                "",
            ),
        )
    else:
        result["v32_direction"] = result[
            direction_column
        ].map(_normalize_direction)

        result.loc[
            result["v32_action"].eq(
                ENTER_LONG
            ),
            "v32_direction",
        ] = LONG

        result.loc[
            result["v32_action"].eq(
                ENTER_SHORT
            ),
            "v32_direction",
        ] = SHORT

    return (
        result.dropna(
            subset=["timestamp"]
        )
        .sort_values(
            [
                "timestamp",
                "asset",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def load_outcome_ensemble(
    path: str | Path,
) -> pd.DataFrame:
    source = Path(path)

    if not source.exists():
        raise FileNotFoundError(
            f"Ensemble decision file does not exist: {source}"
        )

    frame = pd.read_csv(
        source,
        low_memory=False,
    )

    required = {
        "timestamp",
        "asset",
        "v32_action",
        "morphology_state",
        "combined_action",
        "combined_target_exposure",
        "entry_ready",
        "morphology_veto",
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            "Ensemble decisions missing columns: "
            f"{missing}"
        )

    result = frame.copy()

    result["timestamp"] = pd.to_datetime(
        result["timestamp"],
        utc=True,
        errors="coerce",
    )

    result["asset"] = (
        result["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    result["v32_action"] = result[
        "v32_action"
    ].map(_normalize_action)

    result["combined_action"] = result[
        "combined_action"
    ].map(_normalize_action)

    result["combined_target_exposure"] = (
        pd.to_numeric(
            result["combined_target_exposure"],
            errors="coerce",
        )
        .fillna(0.0)
        .clip(lower=0.0)
    )

    result["entry_ready"] = result[
        "entry_ready"
    ].map(_boolean)

    result["morphology_veto"] = result[
        "morphology_veto"
    ].map(_boolean)

    result["morphology_state"] = (
        result["morphology_state"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    return (
        result.dropna(
            subset=["timestamp"]
        )
        .sort_values(
            [
                "timestamp",
                "asset",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def load_outcome_market(
    path: str | Path,
) -> pd.DataFrame:
    source = Path(path)

    if not source.exists():
        raise FileNotFoundError(
            f"Market data does not exist: {source}"
        )

    frame = pd.read_csv(
        source,
        low_memory=False,
    )

    required = {
        "timestamp",
        "asset",
        "close",
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            f"Market data missing columns: {missing}"
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
        .drop_duplicates(
            subset=[
                "asset",
                "timestamp",
            ],
            keep="last",
        )
        .reset_index(drop=True)
    )


def pair_v32_trades(
    v32_stream: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    open_positions: dict[
        str,
        dict[str, Any],
    ] = {}

    for event in v32_stream.to_dict(
        orient="records"
    ):
        asset = str(
            event["asset"]
        )

        action = str(
            event["v32_action"]
        )

        if action in {
            ENTER_LONG,
            ENTER_SHORT,
        }:
            if asset in open_positions:
                continue

            direction = (
                LONG
                if action == ENTER_LONG
                else SHORT
            )

            open_positions[asset] = {
                **event,
                "entry_timestamp":
                    event["timestamp"],
                "direction":
                    direction,
            }

            continue

        if (
            action == EXIT_POSITION
            and asset in open_positions
        ):
            entry = open_positions.pop(
                asset
            )

            rows.append({
                "trade_number":
                    len(rows) + 1,
                "asset":
                    asset,
                "direction":
                    entry["direction"],
                "entry_timestamp":
                    entry["entry_timestamp"],
                "exit_timestamp":
                    event["timestamp"],
                "holding_minutes":
                    (
                        pd.Timestamp(
                            event["timestamp"]
                        )
                        - pd.Timestamp(
                            entry["entry_timestamp"]
                        )
                    ).total_seconds()
                    / 60.0,
                "entry_action":
                    entry["v32_action"],
                "exit_action":
                    action,
                "engine_name":
                    entry.get(
                        "engine_name",
                        entry.get(
                            "source_engine",
                            "",
                        ),
                    ),
            })

    return (
        pd.DataFrame(rows)
        if rows
        else pd.DataFrame()
    )


def attach_trade_prices(
    trades: pd.DataFrame,
    market: pd.DataFrame,
    *,
    config: EnsembleOutcomeConfig,
) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()

    groups: list[pd.DataFrame] = []

    for asset, asset_trades in trades.groupby(
        "asset",
        sort=True,
        observed=True,
    ):
        prices = market[
            market["asset"].eq(asset)
        ][
            [
                "timestamp",
                "close",
            ]
        ].sort_values(
            "timestamp",
            kind="stable",
        )

        if prices.empty:
            continue

        entry_left = (
            asset_trades.sort_values(
                "entry_timestamp",
                kind="stable",
            )
            .reset_index(drop=True)
        )

        entry_right = prices.rename(
            columns={
                "timestamp":
                    "entry_price_timestamp",
                "close":
                    "entry_price",
            }
        )

        priced = pd.merge_asof(
            entry_left,
            entry_right,
            left_on="entry_timestamp",
            right_on="entry_price_timestamp",
            direction="backward",
            tolerance=config.price_tolerance,
            allow_exact_matches=True,
        )

        priced = priced.sort_values(
            "exit_timestamp",
            kind="stable",
        )

        exit_right = prices.rename(
            columns={
                "timestamp":
                    "exit_price_timestamp",
                "close":
                    "exit_price",
            }
        )

        priced = pd.merge_asof(
            priced,
            exit_right,
            left_on="exit_timestamp",
            right_on="exit_price_timestamp",
            direction="backward",
            tolerance=config.price_tolerance,
            allow_exact_matches=True,
        )

        groups.append(
            priced
        )

    if not groups:
        return pd.DataFrame()

    result = pd.concat(
        groups,
        ignore_index=True,
    )

    return (
        result.dropna(
            subset=[
                "entry_price",
                "exit_price",
            ]
        )
        .sort_values(
            "entry_timestamp",
            kind="stable",
        )
        .reset_index(drop=True)
    )


def attach_ensemble_classification(
    trades: pd.DataFrame,
    ensemble: pd.DataFrame,
) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()

    entry_rows = ensemble[
        ensemble[
            "v32_action"
        ].isin({
            ENTER_LONG,
            ENTER_SHORT,
        })
    ].copy()

    keep = [
        column
        for column in (
            "timestamp",
            "asset",
            "ensemble_decision_id",
            "morphology_state",
            "morphology_confidence",
            "morphology_multiplier",
            "morphology_veto",
            "combined_action",
            "combined_direction",
            "combined_target_exposure",
            "entry_ready",
            "reasons",
        )
        if column in entry_rows.columns
    ]

    entry_rows = entry_rows[
        keep
    ].rename(
        columns={
            "timestamp":
                "entry_timestamp",
        }
    )

    result = trades.merge(
        entry_rows,
        on=[
            "entry_timestamp",
            "asset",
        ],
        how="left",
        validate="one_to_one",
    )

    result[
        "morphology_state"
    ] = result[
        "morphology_state"
    ].fillna("UNAVAILABLE")

    result[
        "morphology_veto"
    ] = result[
        "morphology_veto"
    ].fillna(False).map(
        _boolean
    )

    result[
        "entry_ready"
    ] = result[
        "entry_ready"
    ].fillna(False).map(
        _boolean
    )

    result[
        "combined_target_exposure"
    ] = pd.to_numeric(
        result[
            "combined_target_exposure"
        ],
        errors="coerce",
    ).fillna(0.0)

    return result


def calculate_trade_outcomes(
    trades: pd.DataFrame,
    *,
    config: EnsembleOutcomeConfig,
) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()

    result = trades.copy()

    long_mask = result[
        "direction"
    ].eq(LONG)

    short_mask = result[
        "direction"
    ].eq(SHORT)

    result["gross_return"] = 0.0

    result.loc[
        long_mask,
        "gross_return",
    ] = (
        result.loc[
            long_mask,
            "exit_price",
        ]
        / result.loc[
            long_mask,
            "entry_price",
        ]
        - 1.0
    )

    result.loc[
        short_mask,
        "gross_return",
    ] = (
        result.loc[
            short_mask,
            "entry_price",
        ]
        / result.loc[
            short_mask,
            "exit_price",
        ]
        - 1.0
    )

    result["net_return"] = (
        result["gross_return"]
        - config.transaction_cost
    )

    result["baseline_strategy_return"] = (
        result["net_return"]
        * config.baseline_exposure
    )

    result["retained_equal_strategy_return"] = np.where(
        result["entry_ready"].astype(bool),
        result["net_return"]
        * config.baseline_exposure,
        0.0,
    )

    result["ensemble_strategy_return"] = (
        result["net_return"]
        * result[
            "combined_target_exposure"
        ]
    )

    result["vetoed_trade_return"] = np.where(
        result[
            "morphology_veto"
        ].astype(bool),
        result["net_return"],
        np.nan,
    )

    result["veto_avoided_return"] = np.where(
        result[
            "morphology_veto"
        ].astype(bool),
        -result["net_return"],
        0.0,
    )

    result["baseline_win"] = (
        result["net_return"] > 0.0
    )

    result["year"] = pd.to_datetime(
        result["entry_timestamp"],
        utc=True,
    ).dt.year

    return result


def maximum_drawdown(
    returns: pd.Series,
) -> float:
    values = pd.to_numeric(
        returns,
        errors="coerce",
    ).fillna(0.0)

    if values.empty:
        return 0.0

    equity = (
        1.0 + values
    ).cumprod()

    running_peak = equity.cummax()

    drawdown = (
        equity
        / running_peak
        - 1.0
    )

    return float(
        drawdown.min()
    )


def profit_factor(
    returns: pd.Series,
) -> float:
    values = pd.to_numeric(
        returns,
        errors="coerce",
    ).dropna()

    gross_profit = float(
        values[
            values > 0.0
        ].sum()
    )

    gross_loss = abs(
        float(
            values[
                values < 0.0
            ].sum()
        )
    )

    if gross_loss > 0.0:
        return gross_profit / gross_loss

    if gross_profit > 0.0:
        return 100.0

    return 0.0


def summarize_returns(
    frame: pd.DataFrame,
    *,
    return_column: str,
    cohort: str,
) -> dict[str, Any]:
    values = pd.to_numeric(
        frame[return_column],
        errors="coerce",
    ).dropna()

    if values.empty:
        return {
            "cohort": cohort,
            "trade_count": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "mean_return": 0.0,
            "median_return": 0.0,
            "total_compounded_return": 0.0,
            "profit_factor": 0.0,
            "average_winner": 0.0,
            "average_loser": 0.0,
            "maximum_drawdown": 0.0,
            "return_to_drawdown": 0.0,
        }

    wins = values[
        values > 0.0
    ]

    losses = values[
        values < 0.0
    ]

    compounded = float(
        (
            1.0 + values
        ).prod()
        - 1.0
    )

    drawdown = maximum_drawdown(
        values
    )

    return {
        "cohort":
            cohort,
        "trade_count":
            int(len(values)),
        "wins":
            int(len(wins)),
        "losses":
            int(len(losses)),
        "win_rate":
            float(
                len(wins) / len(values)
            ),
        "mean_return":
            float(values.mean()),
        "median_return":
            float(values.median()),
        "total_compounded_return":
            compounded,
        "profit_factor":
            float(
                profit_factor(values)
            ),
        "average_winner":
            float(
                wins.mean()
                if not wins.empty
                else 0.0
            ),
        "average_loser":
            float(
                losses.mean()
                if not losses.empty
                else 0.0
            ),
        "maximum_drawdown":
            drawdown,
        "return_to_drawdown":
            (
                compounded
                / abs(drawdown)
                if drawdown < 0.0
                else 0.0
            ),
    }


def build_cohort_summary(
    trades: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    rows.append(
        summarize_returns(
            trades,
            return_column=(
                "baseline_strategy_return"
            ),
            cohort="BASELINE_V32",
        )
    )

    retained = trades[
        trades[
            "entry_ready"
        ].astype(bool)
    ]

    rows.append(
        summarize_returns(
            retained,
            return_column="net_return",
            cohort="RETAINED_EQUAL_EXPOSURE",
        )
    )

    rows.append(
        summarize_returns(
            trades,
            return_column=(
                "ensemble_strategy_return"
            ),
            cohort="ACTUAL_ENSEMBLE_EXPOSURE",
        )
    )

    vetoed = trades[
        trades[
            "morphology_veto"
        ].astype(bool)
    ]

    rows.append(
        summarize_returns(
            vetoed,
            return_column="net_return",
            cohort="VETOED_V32_TRADES",
        )
    )

    for state in (
        SUPPORTIVE,
        NEUTRAL,
        ADVERSE,
    ):
        cohort = trades[
            trades[
                "morphology_state"
            ].eq(state)
        ]

        rows.append(
            summarize_returns(
                cohort,
                return_column="net_return",
                cohort=f"MORPHOLOGY_{state}",
            )
        )

    for direction in (
        LONG,
        SHORT,
    ):
        cohort = trades[
            trades[
                "direction"
            ].eq(direction)
        ]

        rows.append(
            summarize_returns(
                cohort,
                return_column="net_return",
                cohort=f"BASELINE_{direction}",
            )
        )

    return pd.DataFrame(rows)


def build_yearly_summary(
    trades: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for year, group in trades.groupby(
        "year",
        sort=True,
        observed=True,
    ):
        for column, strategy in (
            (
                "baseline_strategy_return",
                "BASELINE_V32",
            ),
            (
                "retained_equal_strategy_return",
                "RETAINED_EQUAL_EXPOSURE",
            ),
            (
                "ensemble_strategy_return",
                "ACTUAL_ENSEMBLE_EXPOSURE",
            ),
        ):
            summary = summarize_returns(
                group,
                return_column=column,
                cohort=strategy,
            )

            rows.append({
                "year": int(year),
                "strategy": strategy,
                **{
                    key: value
                    for key, value
                    in summary.items()
                    if key != "cohort"
                },
            })

    return pd.DataFrame(rows)


def build_equity_curves(
    trades: pd.DataFrame,
) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()

    result = trades[
        [
            "trade_number",
            "entry_timestamp",
            "exit_timestamp",
            "asset",
            "direction",
            "morphology_state",
            "baseline_strategy_return",
            "retained_equal_strategy_return",
            "ensemble_strategy_return",
        ]
    ].copy()

    result["baseline_equity"] = (
        1.0
        + result[
            "baseline_strategy_return"
        ]
    ).cumprod()

    result["retained_equal_equity"] = (
        1.0
        + result[
            "retained_equal_strategy_return"
        ]
    ).cumprod()

    result["ensemble_equity"] = (
        1.0
        + result[
            "ensemble_strategy_return"
        ]
    ).cumprod()

    result["baseline_drawdown"] = (
        result["baseline_equity"]
        / result[
            "baseline_equity"
        ].cummax()
        - 1.0
    )

    result["retained_equal_drawdown"] = (
        result["retained_equal_equity"]
        / result[
            "retained_equal_equity"
        ].cummax()
        - 1.0
    )

    result["ensemble_drawdown"] = (
        result["ensemble_equity"]
        / result[
            "ensemble_equity"
        ].cummax()
        - 1.0
    )

    return result


def build_outcome_report(
    *,
    trades: pd.DataFrame,
    cohort_summary: pd.DataFrame,
    config: EnsembleOutcomeConfig,
) -> dict[str, Any]:
    def _cohort(name: str) -> dict[str, Any]:
        rows = cohort_summary[
            cohort_summary[
                "cohort"
            ].eq(name)
        ]

        return (
            rows.iloc[0].to_dict()
            if not rows.empty
            else {}
        )

    baseline = _cohort(
        "BASELINE_V32"
    )

    retained = _cohort(
        "RETAINED_EQUAL_EXPOSURE"
    )

    ensemble = _cohort(
        "ACTUAL_ENSEMBLE_EXPOSURE"
    )

    vetoed = _cohort(
        "VETOED_V32_TRADES"
    )

    vetoed_mean = _number(
        vetoed.get(
            "mean_return",
            0.0,
        )
    )

    baseline_mean = _number(
        baseline.get(
            "mean_return",
            0.0,
        )
    )

    retained_mean = _number(
        retained.get(
            "mean_return",
            0.0,
        )
    )

    baseline_drawdown = _number(
        baseline.get(
            "maximum_drawdown",
            0.0,
        )
    )

    ensemble_drawdown = _number(
        ensemble.get(
            "maximum_drawdown",
            0.0,
        )
    )

    return {
        "schema_version":
            "atlas.v32_morphology_ensemble_outcomes.v1",
        "config":
            asdict(config),
        "trade_count":
            int(len(trades)),
        "retained_trade_count":
            int(
                trades[
                    "entry_ready"
                ].astype(bool).sum()
            ),
        "vetoed_trade_count":
            int(
                trades[
                    "morphology_veto"
                ].astype(bool).sum()
            ),
        "supportive_trade_count":
            int(
                trades[
                    "morphology_state"
                ].eq(
                    SUPPORTIVE
                ).sum()
            ),
        "neutral_trade_count":
            int(
                trades[
                    "morphology_state"
                ].eq(
                    NEUTRAL
                ).sum()
            ),
        "adverse_trade_count":
            int(
                trades[
                    "morphology_state"
                ].eq(
                    ADVERSE
                ).sum()
            ),
        "baseline":
            baseline,
        "retained_equal_exposure":
            retained,
        "actual_ensemble_exposure":
            ensemble,
        "vetoed_cohort":
            vetoed,
        "vetoed_cohort_is_negative":
            bool(vetoed_mean < 0.0),
        "retained_mean_exceeds_baseline":
            bool(
                retained_mean
                > baseline_mean
            ),
        "ensemble_drawdown_improved":
            bool(
                ensemble_drawdown
                > baseline_drawdown
            ),
        "morphology_incremental_value_candidate":
            bool(
                vetoed_mean < 0.0
                and retained_mean
                > baseline_mean
                and ensemble_drawdown
                > baseline_drawdown
            ),
        "research_only":
            True,
        "live_authorized":
            False,
        "order_submission_allowed":
            False,
    }


def write_outcome_outputs(
    *,
    trades: pd.DataFrame,
    cohort_summary: pd.DataFrame,
    yearly_summary: pd.DataFrame,
    equity_curves: pd.DataFrame,
    report: dict[str, Any],
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
        "trades":
            directory
            / "v32_morphology_trade_outcomes.csv",
        "cohorts":
            directory
            / "v32_morphology_cohort_summary.csv",
        "yearly":
            directory
            / "v32_morphology_yearly_summary.csv",
        "equity":
            directory
            / "v32_morphology_equity_curves.csv",
        "report":
            directory
            / "v32_morphology_outcome_report.json",
    }

    trades.to_csv(
        outputs["trades"],
        index=False,
    )

    cohort_summary.to_csv(
        outputs["cohorts"],
        index=False,
    )

    yearly_summary.to_csv(
        outputs["yearly"],
        index=False,
    )

    equity_curves.to_csv(
        outputs["equity"],
        index=False,
    )

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


def validate_ensemble_outcomes(
    *,
    v32_stream: pd.DataFrame,
    ensemble: pd.DataFrame,
    market: pd.DataFrame,
    config: EnsembleOutcomeConfig = (
        EnsembleOutcomeConfig()
    ),
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
]:
    trades = pair_v32_trades(
        v32_stream
    )

    trades = attach_trade_prices(
        trades,
        market,
        config=config,
    )

    trades = attach_ensemble_classification(
        trades,
        ensemble,
    )

    trades = calculate_trade_outcomes(
        trades,
        config=config,
    )

    cohorts = build_cohort_summary(
        trades
    )

    yearly = build_yearly_summary(
        trades
    )

    equity = build_equity_curves(
        trades
    )

    report = build_outcome_report(
        trades=trades,
        cohort_summary=cohorts,
        config=config,
    )

    return (
        trades,
        cohorts,
        yearly,
        equity,
        report,
    )
