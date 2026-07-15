"""Morphology Trajectory Execution Engine V2.

Transforms raw trajectory observations into past-only execution intelligence.

For each asset and trajectory path, the engine:
- evaluates only outcomes observed before the current timestamp;
- measures long and short behavior across configured horizons;
- selects the best risk-adjusted direction and holding horizon;
- emits ENTER, AVOID, or INSUFFICIENT_EVIDENCE;
- never authorizes live execution.

The current observation's future outcomes are added to the historical state only
after its recommendation has been produced, preventing look-ahead leakage.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ENTER = "ENTER"
AVOID = "AVOID"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

LONG = "LONG"
SHORT = "SHORT"
FLAT = "FLAT"


@dataclass(frozen=True, slots=True)
class TrajectoryExecutionConfig:
    horizons: tuple[int, ...] = (8, 16, 32)

    minimum_observations: int = 50
    confidence_target: int = 500

    transaction_cost_bps: float = 8.0
    risk_penalty: float = 0.50

    minimum_net_mean_return: float = 0.0
    minimum_win_rate: float = 0.52
    minimum_profit_factor: float = 1.05
    minimum_execution_score: float = 0.0

    maximum_target_exposure: float = 0.10
    research_only: bool = True

    def __post_init__(self) -> None:
        if not self.horizons:
            raise ValueError("At least one horizon is required.")

        if any(int(value) < 1 for value in self.horizons):
            raise ValueError("All horizons must be positive.")

        for name in (
            "minimum_observations",
            "confidence_target",
        ):
            if int(getattr(self, name)) < 1:
                raise ValueError(f"{name} must be positive.")

        if self.transaction_cost_bps < 0.0:
            raise ValueError(
                "transaction_cost_bps cannot be negative."
            )

        if self.risk_penalty < 0.0:
            raise ValueError(
                "risk_penalty cannot be negative."
            )

        if not 0.0 <= self.minimum_win_rate <= 1.0:
            raise ValueError(
                "minimum_win_rate must be between zero and one."
            )

        if self.minimum_profit_factor < 0.0:
            raise ValueError(
                "minimum_profit_factor cannot be negative."
            )

        if not 0.0 <= self.maximum_target_exposure <= 1.0:
            raise ValueError(
                "maximum_target_exposure must be between zero and one."
            )

    @property
    def transaction_cost(self) -> float:
        return self.transaction_cost_bps / 10_000.0


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


def load_trajectory_observations(
    path: str | Path,
    *,
    config: TrajectoryExecutionConfig,
) -> pd.DataFrame:
    source = Path(path)

    if not source.exists():
        raise FileNotFoundError(
            f"Trajectory observation file does not exist: {source}"
        )

    frame = pd.read_csv(
        source,
        low_memory=False,
    )

    required = {
        "trajectory_id",
        "window_end",
        "asset",
        "sequence_length",
        "cluster_path",
        "trajectory_shape",
    }

    for horizon in config.horizons:
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
            "Trajectory observations are missing columns: "
            f"{missing}"
        )

    frame = frame.copy()

    frame["timestamp"] = pd.to_datetime(
        frame["window_end"],
        utc=True,
        errors="coerce",
    )

    frame["asset"] = (
        frame["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    frame["trajectory_id"] = (
        frame["trajectory_id"]
        .astype(str)
        .str.strip()
    )

    numeric_columns: list[str] = []

    for horizon in config.horizons:
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

    return (
        frame.dropna(
            subset=[
                "timestamp",
                "asset",
                "trajectory_id",
            ]
        )
        .sort_values(
            [
                "timestamp",
                "asset",
                "sequence_length",
                "trajectory_id",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def _empty_statistics() -> dict[str, float]:
    return {
        "count": 0.0,
        "return_sum": 0.0,
        "win_count": 0.0,
        "gross_profit": 0.0,
        "gross_loss": 0.0,
        "mfe_sum": 0.0,
        "mae_sum": 0.0,
    }


def _update_statistics(
    statistics: dict[str, float],
    *,
    realized_return: float,
    mfe: float,
    mae: float,
) -> None:
    if not math.isfinite(realized_return):
        return

    statistics["count"] += 1.0
    statistics["return_sum"] += realized_return

    if realized_return > 0.0:
        statistics["win_count"] += 1.0
        statistics["gross_profit"] += realized_return
    elif realized_return < 0.0:
        statistics["gross_loss"] += abs(realized_return)

    statistics["mfe_sum"] += max(
        _number(mfe),
        0.0,
    )

    statistics["mae_sum"] += abs(
        min(
            _number(mae),
            0.0,
        )
    )


def _statistics_metrics(
    statistics: dict[str, float],
    *,
    config: TrajectoryExecutionConfig,
) -> dict[str, float]:
    count = int(
        statistics["count"]
    )

    if count <= 0:
        return {
            "observation_count": 0,
            "mean_return": 0.0,
            "net_mean_return": 0.0,
            "win_rate": 0.0,
            "mean_mfe": 0.0,
            "mean_mae": 0.0,
            "profit_factor": 0.0,
            "reward_risk": 0.0,
            "risk_adjusted_edge": 0.0,
            "confidence": 0.0,
            "execution_score": 0.0,
        }

    mean_return = (
        statistics["return_sum"]
        / count
    )

    net_mean_return = (
        mean_return
        - config.transaction_cost
    )

    win_rate = (
        statistics["win_count"]
        / count
    )

    mean_mfe = (
        statistics["mfe_sum"]
        / count
    )

    mean_mae = (
        statistics["mae_sum"]
        / count
    )

    if statistics["gross_loss"] > 0.0:
        profit_factor = (
            statistics["gross_profit"]
            / statistics["gross_loss"]
        )
    elif statistics["gross_profit"] > 0.0:
        profit_factor = 100.0
    else:
        profit_factor = 0.0

    reward_risk = (
        mean_mfe
        / max(
            mean_mae,
            1e-12,
        )
    )

    risk_adjusted_edge = (
        net_mean_return
        - config.risk_penalty
        * mean_mae
    )

    sample_confidence = min(
        count
        / config.confidence_target,
        1.0,
    )

    win_quality = float(
        np.clip(
            (
                win_rate
                - 0.50
            )
            / 0.20,
            0.0,
            1.0,
        )
    )

    profit_factor_quality = float(
        np.clip(
            (
                profit_factor
                - 1.0
            )
            / 1.5,
            0.0,
            1.0,
        )
    )

    confidence = (
        sample_confidence
        * (
            0.50
            + 0.25 * win_quality
            + 0.25 * profit_factor_quality
        )
    )

    execution_score = (
        max(
            risk_adjusted_edge,
            0.0,
        )
        * confidence
    )

    return {
        "observation_count": count,
        "mean_return": mean_return,
        "net_mean_return": net_mean_return,
        "win_rate": win_rate,
        "mean_mfe": mean_mfe,
        "mean_mae": -mean_mae,
        "profit_factor": profit_factor,
        "reward_risk": reward_risk,
        "risk_adjusted_edge": risk_adjusted_edge,
        "confidence": confidence,
        "execution_score": execution_score,
    }


def _state_key(
    row: dict[str, Any],
) -> tuple[str, str]:
    return (
        str(row["asset"]),
        str(row["trajectory_id"]),
    )


def _decision_id(
    payload: dict[str, Any],
) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()[:24]

    return f"TRAJ-EXEC-V2-{digest}"


def _best_candidate(
    state: dict[
        tuple[int, str],
        dict[str, float],
    ],
    *,
    config: TrajectoryExecutionConfig,
) -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []

    for horizon in config.horizons:
        for direction in (
            LONG,
            SHORT,
        ):
            statistics = state.get(
                (
                    horizon,
                    direction,
                )
            )

            if statistics is None:
                continue

            metrics = _statistics_metrics(
                statistics,
                config=config,
            )

            if (
                metrics["observation_count"]
                < config.minimum_observations
            ):
                continue

            candidates.append({
                "horizon_bars": horizon,
                "direction": direction,
                **metrics,
            })

    if not candidates:
        return None

    candidates.sort(
        key=lambda candidate: (
            candidate["execution_score"],
            candidate["risk_adjusted_edge"],
            candidate["net_mean_return"],
            candidate["observation_count"],
            -candidate["horizon_bars"],
        ),
        reverse=True,
    )

    return candidates[0]


def build_trajectory_execution_signals(
    observations: pd.DataFrame,
    *,
    config: TrajectoryExecutionConfig = (
        TrajectoryExecutionConfig()
    ),
) -> pd.DataFrame:
    historical_state: dict[
        tuple[str, str],
        dict[
            tuple[int, str],
            dict[str, float],
        ],
    ] = {}

    rows: list[dict[str, Any]] = []

    for source in observations.to_dict(
        orient="records"
    ):
        key = _state_key(
            source
        )

        trajectory_state = (
            historical_state.setdefault(
                key,
                {},
            )
        )

        candidate = _best_candidate(
            trajectory_state,
            config=config,
        )

        if candidate is None:
            action = INSUFFICIENT_EVIDENCE
            direction = FLAT
            entry_ready = False

            candidate = {
                "horizon_bars": 0,
                "direction": FLAT,
                "observation_count": 0,
                "mean_return": 0.0,
                "net_mean_return": 0.0,
                "win_rate": 0.0,
                "mean_mfe": 0.0,
                "mean_mae": 0.0,
                "profit_factor": 0.0,
                "reward_risk": 0.0,
                "risk_adjusted_edge": 0.0,
                "confidence": 0.0,
                "execution_score": 0.0,
            }

            reasons = [
                "minimum_history_not_met",
            ]
        else:
            passed = bool(
                candidate["net_mean_return"]
                > config.minimum_net_mean_return
                and candidate["win_rate"]
                >= config.minimum_win_rate
                and candidate["profit_factor"]
                >= config.minimum_profit_factor
                and candidate["execution_score"]
                > config.minimum_execution_score
            )

            if passed:
                action = ENTER
                direction = candidate[
                    "direction"
                ]
                entry_ready = True

                reasons = [
                    "past_only_trajectory_edge",
                    "minimum_history_met",
                    "positive_net_expectancy",
                ]
            else:
                action = AVOID
                direction = FLAT
                entry_ready = False

                reasons = [
                    "minimum_history_met",
                    "trajectory_edge_below_threshold",
                ]

        confidence = float(
            candidate["confidence"]
        )

        target_exposure = (
            config.maximum_target_exposure
            * confidence
            if entry_ready
            else 0.0
        )

        payload = {
            "schema_version":
                "atlas.morphology_trajectory_execution.v2",
            "timestamp":
                pd.Timestamp(
                    source["timestamp"]
                ).isoformat(),
            "window_start":
                source.get(
                    "window_start",
                    "",
                ),
            "window_end":
                source.get(
                    "window_end",
                    "",
                ),
            "asset":
                str(
                    source["asset"]
                ),
            "trajectory_id":
                str(
                    source["trajectory_id"]
                ),
            "sequence_length":
                int(
                    _number(
                        source.get(
                            "sequence_length",
                            0,
                        )
                    )
                ),
            "cluster_path":
                str(
                    source.get(
                        "cluster_path",
                        "",
                    )
                ),
            "cluster_name_path":
                str(
                    source.get(
                        "cluster_name_path",
                        "",
                    )
                ),
            "trajectory_shape":
                str(
                    source.get(
                        "trajectory_shape",
                        "",
                    )
                ),
            "recommended_action":
                action,
            "recommended_direction":
                direction,
            "entry_ready":
                entry_ready,
            "optimal_horizon_bars":
                int(
                    candidate[
                        "horizon_bars"
                    ]
                ),
            "observation_count":
                int(
                    candidate[
                        "observation_count"
                    ]
                ),
            "preferred_mean_return":
                float(
                    candidate[
                        "net_mean_return"
                    ]
                ),
            "preferred_gross_mean_return":
                float(
                    candidate[
                        "mean_return"
                    ]
                ),
            "preferred_win_rate":
                float(
                    candidate[
                        "win_rate"
                    ]
                ),
            "preferred_mean_mfe":
                float(
                    candidate[
                        "mean_mfe"
                    ]
                ),
            "preferred_mean_mae":
                float(
                    candidate[
                        "mean_mae"
                    ]
                ),
            "preferred_profit_factor":
                float(
                    candidate[
                        "profit_factor"
                    ]
                ),
            "preferred_reward_risk":
                float(
                    candidate[
                        "reward_risk"
                    ]
                ),
            "risk_adjusted_edge":
                float(
                    candidate[
                        "risk_adjusted_edge"
                    ]
                ),
            "trajectory_score":
                float(
                    candidate[
                        "execution_score"
                    ]
                ),
            "confidence":
                confidence,
            "target_exposure":
                float(
                    target_exposure
                ),
            "reasons":
                "|".join(
                    reasons
                ),
            "research_only":
                bool(
                    config.research_only
                ),
            "live_authorized":
                False,
            "order_submission_allowed":
                False,
        }

        payload["decision_id"] = (
            _decision_id(
                payload
            )
        )

        rows.append(
            payload
        )

        # Update state only after generating the current recommendation.
        # This prevents the current row's future return from influencing itself.
        for horizon in config.horizons:
            long_statistics = (
                trajectory_state.setdefault(
                    (
                        horizon,
                        LONG,
                    ),
                    _empty_statistics(),
                )
            )

            short_statistics = (
                trajectory_state.setdefault(
                    (
                        horizon,
                        SHORT,
                    ),
                    _empty_statistics(),
                )
            )

            _update_statistics(
                long_statistics,
                realized_return=_number(
                    source.get(
                        f"forward_return_{horizon}",
                        float("nan"),
                    ),
                    float("nan"),
                ),
                mfe=_number(
                    source.get(
                        f"long_mfe_{horizon}",
                        0.0,
                    )
                ),
                mae=_number(
                    source.get(
                        f"long_mae_{horizon}",
                        0.0,
                    )
                ),
            )

            _update_statistics(
                short_statistics,
                realized_return=_number(
                    source.get(
                        f"short_return_{horizon}",
                        float("nan"),
                    ),
                    float("nan"),
                ),
                mfe=_number(
                    source.get(
                        f"short_mfe_{horizon}",
                        0.0,
                    )
                ),
                mae=_number(
                    source.get(
                        f"short_mae_{horizon}",
                        0.0,
                    )
                ),
            )

    if not rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "timestamp",
                "asset",
                "sequence_length",
                "trajectory_id",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def write_trajectory_execution_outputs(
    *,
    signals: pd.DataFrame,
    config: TrajectoryExecutionConfig,
    output_dir: str | Path,
) -> dict[str, Path]:
    directory = Path(
        output_dir
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = (
        directory
        / "morphology_trajectory_execution_signals.csv"
    )

    summary_path = (
        directory
        / "morphology_trajectory_execution_summary.json"
    )

    latest_path = (
        directory
        / "morphology_trajectory_execution_latest.csv"
    )

    signals.to_csv(
        csv_path,
        index=False,
    )

    if signals.empty:
        latest = signals.copy()
    else:
        latest_timestamp = signals[
            "timestamp"
        ].max()

        latest = signals[
            signals[
                "timestamp"
            ].eq(
                latest_timestamp
            )
        ].copy()

    latest.to_csv(
        latest_path,
        index=False,
    )

    summary = {
        "schema_version":
            "atlas.morphology_trajectory_execution_summary.v2",
        "config":
            asdict(config),
        "signal_rows":
            int(len(signals)),
        "entry_rows":
            int(
                signals[
                    "entry_ready"
                ].astype(bool).sum()
            ) if not signals.empty else 0,
        "avoid_rows":
            int(
                signals[
                    "recommended_action"
                ].eq(AVOID).sum()
            ) if not signals.empty else 0,
        "insufficient_evidence_rows":
            int(
                signals[
                    "recommended_action"
                ].eq(
                    INSUFFICIENT_EVIDENCE
                ).sum()
            ) if not signals.empty else 0,
        "long_entries":
            int(
                (
                    signals[
                        "entry_ready"
                    ].astype(bool)
                    & signals[
                        "recommended_direction"
                    ].eq(LONG)
                ).sum()
            ) if not signals.empty else 0,
        "short_entries":
            int(
                (
                    signals[
                        "entry_ready"
                    ].astype(bool)
                    & signals[
                        "recommended_direction"
                    ].eq(SHORT)
                ).sum()
            ) if not signals.empty else 0,
        "research_only":
            True,
        "live_authorized":
            False,
        "order_submission_allowed":
            False,
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
        "signals":
            csv_path,
        "latest":
            latest_path,
        "summary":
            summary_path,
    }
