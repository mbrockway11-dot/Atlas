"""Tests for Historical Governance Snapshots v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.governance_snapshots.builder import (
    build_context_snapshot,
    build_engine_snapshot,
    determine_effective_at,
)
from atlas.investment.governance_snapshots.storage import (
    governance_map_as_of,
    resolve_governance_as_of,
)


def research() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "engine_id": "engine_a",
            "family": "trend",
            "decision": "PROMOTE",
            "promotion_score": 0.80,
            "hard_failures": "",
        },
        {
            "engine_id": "engine_b",
            "family": "mean_reversion",
            "decision": "RETIRE",
            "promotion_score": 0.30,
            "hard_failures": (
                "NONPOSITIVE_EXPECTANCY"
            ),
        },
    ])


def governance() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "engine_id": "engine_a",
            "family": "trend",
            "decision": "PROMOTE",
            "eligible": True,
            "governance_weight": 1.0,
            "base_governance_weight": 0.8,
            "diversification_modifier": 1.0,
            "combined_modifier": 1.1,
            "hard_failures": "",
        },
        {
            "engine_id": "engine_b",
            "family": "mean_reversion",
            "decision": "RETIRE",
            "eligible": False,
            "governance_weight": 0.0,
            "base_governance_weight": 0.0,
            "diversification_modifier": 0.0,
            "combined_modifier": 0.0,
            "hard_failures": (
                "NONPOSITIVE_EXPECTANCY"
            ),
        },
    ])


def test_effective_date_uses_market_timestamp():
    market = pd.DataFrame([
        {
            "timestamp": (
                "2026-07-10T00:00:00+00:00"
            )
        }
    ])

    result = determine_effective_at(
        market
    )

    assert (
        result.isoformat()
        == "2026-07-10T00:00:00+00:00"
    )


def test_engine_snapshot_preserves_eligibility():
    snapshot = build_engine_snapshot(
        effective_at=pd.Timestamp(
            "2026-07-10",
            tz="UTC",
        ),
        captured_at=(
            "2026-07-11T12:00:00+00:00"
        ),
        research=research(),
        learning=pd.DataFrame(),
        regime=pd.DataFrame(),
        fusion=pd.DataFrame(),
        governance=governance(),
    ).set_index("engine_id")

    assert bool(
        snapshot.loc[
            "engine_a",
            "eligible",
        ]
    )

    assert not bool(
        snapshot.loc[
            "engine_b",
            "eligible",
        ]
    )


def test_governance_map_resolves_point_in_time():
    first = build_engine_snapshot(
        effective_at=pd.Timestamp(
            "2026-07-01",
            tz="UTC",
        ),
        captured_at=(
            "2026-07-01T12:00:00+00:00"
        ),
        research=research(),
        learning=pd.DataFrame(),
        regime=pd.DataFrame(),
        fusion=pd.DataFrame(),
        governance=governance(),
    )

    second_governance = governance()
    second_governance.loc[
        second_governance[
            "engine_id"
        ].eq("engine_a"),
        "governance_weight",
    ] = 0.75

    second = build_engine_snapshot(
        effective_at=pd.Timestamp(
            "2026-07-10",
            tz="UTC",
        ),
        captured_at=(
            "2026-07-10T12:00:00+00:00"
        ),
        research=research(),
        learning=pd.DataFrame(),
        regime=pd.DataFrame(),
        fusion=pd.DataFrame(),
        governance=second_governance,
    )

    history = pd.concat(
        [
            first,
            second,
        ],
        ignore_index=True,
    )

    resolved = resolve_governance_as_of(
        history,
        pd.Timestamp(
            "2026-07-05",
            tz="UTC",
        ),
    )

    assert not resolved.empty

    mapping = governance_map_as_of(
        history,
        pd.Timestamp(
            "2026-07-12",
            tz="UTC",
        ),
    )

    assert set(mapping) == {
        "engine_a"
    }

    assert round(
        sum(mapping.values()),
        8,
    ) == 1.0


def test_context_snapshot_has_bounded_controls():
    snapshot = build_context_snapshot(
        effective_at=pd.Timestamp(
            "2026-07-10",
            tz="UTC",
        ),
        captured_at=(
            "2026-07-11T12:00:00+00:00"
        ),
        macro_report={
            "macro_environment": {
                "macro_regime": (
                    "RESTRICTIVE_STABILITY"
                ),
                "confidence": 0.60,
            }
        },
        regime_report={
            "regime": {
                "regime": "TRANSITION",
                "confidence": 0.60,
            }
        },
        fusion_report={
            "fused_context": {
                "fused_regime": (
                    "RESTRICTIVE_TRANSITION"
                ),
                "confidence": 0.60,
                "controls": {
                    "minimum_cash_weight": 0.35,
                },
            }
        },
    )

    assert (
        float(
            snapshot.iloc[0][
                "minimum_cash_weight"
            ]
        )
        == 0.35
    )


def test_snapshot_fingerprints_are_deterministic():
    kwargs = {
        "effective_at": pd.Timestamp(
            "2026-07-10",
            tz="UTC",
        ),
        "captured_at": (
            "2026-07-11T12:00:00+00:00"
        ),
        "research": research(),
        "learning": pd.DataFrame(),
        "regime": pd.DataFrame(),
        "fusion": pd.DataFrame(),
        "governance": governance(),
    }

    first = build_engine_snapshot(
        **kwargs
    )

    second = build_engine_snapshot(
        **kwargs
    )

    assert (
        first["snapshot_id"].tolist()
        == second[
            "snapshot_id"
        ].tolist()
    )
