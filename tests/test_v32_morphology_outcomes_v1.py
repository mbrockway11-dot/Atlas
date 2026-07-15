from __future__ import annotations

import pandas as pd

from atlas.investment.morphology_intelligence.ensemble_outcomes import (
    EnsembleOutcomeConfig,
    pair_v32_trades,
    validate_ensemble_outcomes,
)


def _v32() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T00:00:00Z"
                ),
            "asset":
                "SOL",
            "v32_action":
                "ENTER_LONG",
            "v32_direction":
                "LONG",
        },
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T01:00:00Z"
                ),
            "asset":
                "SOL",
            "v32_action":
                "EXIT_POSITION",
            "v32_direction":
                "",
        },
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-02T00:00:00Z"
                ),
            "asset":
                "SOL",
            "v32_action":
                "ENTER_SHORT",
            "v32_direction":
                "SHORT",
        },
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-02T01:00:00Z"
                ),
            "asset":
                "SOL",
            "v32_action":
                "EXIT_POSITION",
            "v32_direction":
                "",
        },
    ])


def _ensemble() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T00:00:00Z"
                ),
            "asset":
                "SOL",
            "v32_action":
                "ENTER_LONG",
            "morphology_state":
                "SUPPORTIVE",
            "morphology_confidence":
                0.8,
            "morphology_multiplier":
                1.0,
            "morphology_veto":
                False,
            "combined_action":
                "ENTER_LONG",
            "combined_direction":
                "LONG",
            "combined_target_exposure":
                0.10,
            "entry_ready":
                True,
            "reasons":
                "support",
        },
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-02T00:00:00Z"
                ),
            "asset":
                "SOL",
            "v32_action":
                "ENTER_SHORT",
            "morphology_state":
                "ADVERSE",
            "morphology_confidence":
                0.2,
            "morphology_multiplier":
                0.0,
            "morphology_veto":
                True,
            "combined_action":
                "NO_ACTION",
            "combined_direction":
                "FLAT",
            "combined_target_exposure":
                0.0,
            "entry_ready":
                False,
            "reasons":
                "veto",
        },
    ])


def _market() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T00:00:00Z"
                ),
            "asset":
                "SOL",
            "close":
                100.0,
        },
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T01:00:00Z"
                ),
            "asset":
                "SOL",
            "close":
                110.0,
        },
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-02T00:00:00Z"
                ),
            "asset":
                "SOL",
            "close":
                100.0,
        },
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-02T01:00:00Z"
                ),
            "asset":
                "SOL",
            "close":
                110.0,
        },
    ])


def test_entry_exit_pairing() -> None:
    trades = pair_v32_trades(
        _v32()
    )

    assert len(trades) == 2
    assert trades.iloc[0]["direction"] == "LONG"
    assert trades.iloc[1]["direction"] == "SHORT"


def test_outcome_validator_builds_all_outputs() -> None:
    (
        trades,
        cohorts,
        yearly,
        equity,
        report,
    ) = validate_ensemble_outcomes(
        v32_stream=_v32(),
        ensemble=_ensemble(),
        market=_market(),
        config=EnsembleOutcomeConfig(
            transaction_cost_bps=0.0,
        ),
    )

    assert len(trades) == 2
    assert not cohorts.empty
    assert not yearly.empty
    assert not equity.empty

    assert int(
        report[
            "retained_trade_count"
        ]
    ) == 1

    assert int(
        report[
            "vetoed_trade_count"
        ]
    ) == 1


def test_vetoed_short_trade_is_negative() -> None:
    (
        trades,
        _,
        _,
        _,
        report,
    ) = validate_ensemble_outcomes(
        v32_stream=_v32(),
        ensemble=_ensemble(),
        market=_market(),
        config=EnsembleOutcomeConfig(
            transaction_cost_bps=0.0,
        ),
    )

    vetoed = trades[
        trades[
            "morphology_veto"
        ].astype(bool)
    ]

    assert vetoed.iloc[0][
        "net_return"
    ] < 0.0

    assert bool(
        report[
            "vetoed_cohort_is_negative"
        ]
    )


def test_ensemble_never_grants_live_authorization() -> None:
    (
        _,
        _,
        _,
        _,
        report,
    ) = validate_ensemble_outcomes(
        v32_stream=_v32(),
        ensemble=_ensemble(),
        market=_market(),
        config=EnsembleOutcomeConfig(),
    )

    assert not bool(
        report["live_authorized"]
    )

    assert not bool(
        report[
            "order_submission_allowed"
        ]
    )
