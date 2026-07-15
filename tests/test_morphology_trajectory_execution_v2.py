from __future__ import annotations

import pandas as pd

from atlas.investment.morphology_intelligence.trajectory_execution_v2 import (
    ENTER,
    INSUFFICIENT_EVIDENCE,
    LONG,
    SHORT,
    TrajectoryExecutionConfig,
    build_trajectory_execution_signals,
)


def _observations(
    *,
    count: int = 12,
    long_return: float = 0.01,
) -> pd.DataFrame:
    rows = []

    for index in range(count):
        rows.append({
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T00:00:00Z"
                )
                + pd.Timedelta(
                    minutes=15 * index
                ),
            "window_start":
                "",
            "window_end":
                "",
            "asset":
                "SOL",
            "trajectory_id":
                "TRAJ-TEST",
            "sequence_length":
                3,
            "cluster_path":
                "1->2->3",
            "cluster_name_path":
                "",
            "trajectory_shape":
                "PROGRESSIVE",
            "forward_return_8":
                long_return,
            "short_return_8":
                -long_return,
            "long_mfe_8":
                abs(long_return) * 1.5,
            "long_mae_8":
                -abs(long_return) * 0.20,
            "short_mfe_8":
                abs(long_return) * 0.20,
            "short_mae_8":
                -abs(long_return) * 1.5,
        })

    return pd.DataFrame(rows)


def _config() -> TrajectoryExecutionConfig:
    return TrajectoryExecutionConfig(
        horizons=(8,),
        minimum_observations=5,
        confidence_target=10,
        transaction_cost_bps=0.0,
        risk_penalty=0.10,
        minimum_win_rate=0.50,
        minimum_profit_factor=1.0,
    )


def test_first_observation_has_no_prior_evidence() -> None:
    signals = build_trajectory_execution_signals(
        _observations(),
        config=_config(),
    )

    assert (
        signals.iloc[0][
            "recommended_action"
        ]
        == INSUFFICIENT_EVIDENCE
    )


def test_positive_long_history_produces_long_entry() -> None:
    signals = build_trajectory_execution_signals(
        _observations(
            long_return=0.01,
        ),
        config=_config(),
    )

    eligible = signals[
        signals["entry_ready"].astype(bool)
    ]

    assert not eligible.empty
    assert eligible.iloc[-1][
        "recommended_action"
    ] == ENTER
    assert eligible.iloc[-1][
        "recommended_direction"
    ] == LONG


def test_positive_short_history_produces_short_entry() -> None:
    signals = build_trajectory_execution_signals(
        _observations(
            long_return=-0.01,
        ),
        config=_config(),
    )

    eligible = signals[
        signals["entry_ready"].astype(bool)
    ]

    assert not eligible.empty
    assert eligible.iloc[-1][
        "recommended_direction"
    ] == SHORT


def test_current_outcome_does_not_influence_current_signal() -> None:
    observations = _observations(
        count=7,
        long_return=0.01,
    )

    first = build_trajectory_execution_signals(
        observations,
        config=_config(),
    )

    observations.loc[
        observations.index[-1],
        "forward_return_8",
    ] = -1.0

    observations.loc[
        observations.index[-1],
        "short_return_8",
    ] = 1.0

    second = build_trajectory_execution_signals(
        observations,
        config=_config(),
    )

    assert (
        first.iloc[-1][
            "recommended_direction"
        ]
        == second.iloc[-1][
            "recommended_direction"
        ]
    )


def test_engine_never_authorizes_live_orders() -> None:
    signals = build_trajectory_execution_signals(
        _observations(),
        config=_config(),
    )

    assert not signals[
        "live_authorized"
    ].astype(bool).any()

    assert not signals[
        "order_submission_allowed"
    ].astype(bool).any()


def test_decision_ids_are_deterministic() -> None:
    first = build_trajectory_execution_signals(
        _observations(),
        config=_config(),
    )

    second = build_trajectory_execution_signals(
        _observations(),
        config=_config(),
    )

    assert first[
        "decision_id"
    ].tolist() == second[
        "decision_id"
    ].tolist()
