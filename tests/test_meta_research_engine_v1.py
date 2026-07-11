"""Tests for Meta Research Engine v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.meta_research.diagnostics import (
    build_engine_diagnostics,
)
from atlas.investment.meta_research.evidence import (
    build_research_evidence,
)
from atlas.investment.meta_research.failure_modes import (
    build_engine_failure_modes,
)
from atlas.investment.meta_research.family_gaps import (
    build_engine_family_gaps,
)
from atlas.investment.meta_research.hypotheses import (
    build_hypothesis_library,
)
from atlas.investment.meta_research.interactions import (
    build_feature_interactions,
)


def trades() -> pd.DataFrame:
    rows = []

    for day in range(90):
        timestamp = (
            pd.Timestamp(
                "2025-01-01",
                tz="UTC",
            )
            + pd.Timedelta(
                days=day
            )
        )

        high_volatility = (
            day % 3 == 0
        )

        strategy_return = (
            -0.025
            if high_volatility
            else 0.018
        )

        rows.append({
            "engine_id": "trend_test_v1",
            "engine_version": "1.0.0",
            "family": "trend",
            "timestamp": timestamp,
            "date": timestamp,
            "asset": "BTC-USD",
            "direction": "LONG",
            "signal": "LONG",
            "holding_period": 7,
            "strategy_return": (
                strategy_return
            ),
            "forward_return": (
                strategy_return
            ),
            "normalized_score": 0.70,
            "confidence": 0.80,
            "conviction": 0.56,
            "regime": "TEST",
            "reason_codes": "",
        })

    return pd.DataFrame(rows)


def market_history() -> pd.DataFrame:
    rows = []

    for day in range(90):
        timestamp = (
            pd.Timestamp(
                "2025-01-01",
                tz="UTC",
            )
            + pd.Timedelta(
                days=day
            )
        )

        rows.append({
            "timestamp": timestamp,
            "asset": "BTC-USD",
            "close": 100 + day,
            "return_30d": (
                -0.10
                if day % 3 == 0
                else 0.15
            ),
            "momentum_30d": (
                -0.08
                if day % 3 == 0
                else 0.12
            ),
            "volatility_30d": (
                0.90
                if day % 3 == 0
                else 0.25
            ),
            "drawdown_from_90d_high": (
                -0.30
                if day % 3 == 0
                else -0.05
            ),
            "trend_state": (
                "DOWNTREND"
                if day % 3 == 0
                else "UPTREND"
            ),
            "volatility_state": (
                "HIGH"
                if day % 3 == 0
                else "NORMAL"
            ),
            "liquidity_state": "NORMAL",
        })

    return pd.DataFrame(rows)


def test_evidence_joins_contemporaneous_features():
    evidence = build_research_evidence(
        trades(),
        market_history(),
    )

    assert len(evidence) == 90

    assert (
        "volatility_30d"
        in evidence.columns
    )

    assert evidence[
        "strategy_return"
    ].notna().all()


def test_engine_diagnostics_are_deterministic():
    evidence = build_research_evidence(
        trades(),
        market_history(),
    )

    first = build_engine_diagnostics(
        evidence
    )

    second = build_engine_diagnostics(
        evidence
    )

    pd.testing.assert_frame_equal(
        first,
        second,
    )


def test_feature_interactions_find_states():
    evidence = build_research_evidence(
        trades(),
        market_history(),
    )

    interactions = (
        build_feature_interactions(
            evidence
        )
    )

    volatility_rows = interactions[
        interactions["feature"].eq(
            "volatility_30d"
        )
    ]

    assert not volatility_rows.empty

    assert set(
        volatility_rows["state"]
    ).issubset({
        "LOW",
        "MID",
        "HIGH",
    })


def test_failure_modes_are_detected():
    evidence = build_research_evidence(
        trades(),
        market_history(),
    )

    interactions = (
        build_feature_interactions(
            evidence
        )
    )

    failures = build_engine_failure_modes(
        interactions
    )

    assert not failures.empty

    assert (
        failures[
            "engine_id"
        ].eq(
            "trend_test_v1"
        ).any()
    )


def test_family_gaps_include_missing_families():
    evidence = build_research_evidence(
        trades(),
        market_history(),
    )

    diagnostics = build_engine_diagnostics(
        evidence
    )

    gaps = build_engine_family_gaps(
        diagnostics,
        pd.DataFrame([
            {
                "engine_id": (
                    "trend_test_v1"
                ),
                "family": "trend",
                "decision": "KEEP",
            }
        ]),
        pd.DataFrame(),
    )

    breakout = gaps[
        gaps["family"].eq(
            "breakout"
        )
    ]

    assert not breakout.empty

    assert (
        breakout.iloc[0][
            "coverage_status"
        ]
        == "MISSING_FAMILY"
    )


def test_hypotheses_never_issue_execution():
    evidence = build_research_evidence(
        trades(),
        market_history(),
    )

    interactions = (
        build_feature_interactions(
            evidence
        )
    )

    failures = build_engine_failure_modes(
        interactions
    )

    gaps = build_engine_family_gaps(
        build_engine_diagnostics(
            evidence
        ),
        pd.DataFrame(),
        pd.DataFrame(),
    )

    hypotheses = build_hypothesis_library(
        interactions,
        failures,
        gaps,
    )

    assert not hypotheses.empty

    assert not hypotheses[
        "execution_instruction"
    ].astype(bool).any()
