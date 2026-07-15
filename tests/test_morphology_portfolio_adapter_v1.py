from __future__ import annotations

import pandas as pd

from atlas.investment.morphology_intelligence.portfolio_adapter import (
    MorphologyPortfolioAdapterConfig,
    build_morphology_portfolio_targets,
)


def _decisions() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "decision_id":
                "DEC-SOL",
            "timestamp":
                "2026-01-01T00:00:00+00:00",
            "asset":
                "SOL",
            "action":
                "ENTER",
            "direction":
                "LONG",
            "entry_ready":
                True,
            "confidence":
                0.90,
            "target_exposure":
                0.10,
            "validation_weighted_uplift":
                0.003,
            "research_only":
                True,
            "live_authorized":
                False,
        },
        {
            "decision_id":
                "DEC-ETH",
            "timestamp":
                "2026-01-01T00:00:00+00:00",
            "asset":
                "ETH",
            "action":
                "ENTER",
            "direction":
                "LONG",
            "entry_ready":
                True,
            "confidence":
                0.80,
            "target_exposure":
                0.08,
            "validation_weighted_uplift":
                0.002,
            "research_only":
                True,
            "live_authorized":
                False,
        },
        {
            "decision_id":
                "DEC-BTC",
            "timestamp":
                "2026-01-01T00:00:00+00:00",
            "asset":
                "BTC",
            "action":
                "AVOID",
            "direction":
                "FLAT",
            "entry_ready":
                False,
            "confidence":
                0.40,
            "target_exposure":
                0.0,
            "validation_weighted_uplift":
                0.0,
            "research_only":
                True,
            "live_authorized":
                False,
        },
    ])


def test_adapter_selects_highest_conviction() -> None:
    targets = build_morphology_portfolio_targets(
        _decisions(),
        config=MorphologyPortfolioAdapterConfig(
            maximum_total_exposure=0.10,
            maximum_asset_exposure=0.10,
            maximum_positions=1,
            minimum_confidence=0.70,
        ),
    )

    assets = targets[
        ~targets["asset"].eq("CASH")
    ]

    assert len(assets) == 1
    assert assets.iloc[0]["asset"] == "SOL"


def test_total_exposure_is_hard_capped() -> None:
    targets = build_morphology_portfolio_targets(
        _decisions(),
        config=MorphologyPortfolioAdapterConfig(
            maximum_total_exposure=0.10,
            maximum_asset_exposure=0.08,
            maximum_positions=2,
            minimum_confidence=0.70,
        ),
    )

    assets = targets[
        ~targets["asset"].eq("CASH")
    ]

    assert (
        assets[
            "target_weight"
        ].abs().sum()
        <= 0.10 + 1e-12
    )

    assert (
        assets[
            "target_weight"
        ].abs().max()
        <= 0.08 + 1e-12
    )


def test_adapter_never_authorizes_orders() -> None:
    targets = build_morphology_portfolio_targets(
        _decisions()
    )

    assert not targets[
        "live_authorized"
    ].astype(bool).any()

    assert not targets[
        "order_submission_allowed"
    ].astype(bool).any()

    assert targets[
        "requires_pre_trade_risk"
    ].astype(bool).all()

    assert targets[
        "requires_manual_approval"
    ].astype(bool).all()


def test_no_entries_produces_cash_only() -> None:
    decisions = _decisions().copy()

    decisions[
        "entry_ready"
    ] = False

    targets = build_morphology_portfolio_targets(
        decisions
    )

    assert targets[
        "asset"
    ].tolist() == [
        "CASH",
    ]

    assert targets.iloc[0][
        "target_weight"
    ] == 1.0


def test_batch_id_is_deterministic() -> None:
    first = build_morphology_portfolio_targets(
        _decisions()
    )

    second = build_morphology_portfolio_targets(
        _decisions()
    )

    assert first[
        "portfolio_batch_id"
    ].tolist() == second[
        "portfolio_batch_id"
    ].tolist()
