"""Integration tests for G.8 execution provenance."""

from __future__ import annotations

from atlas.investment.execution import (
    AccountSnapshot,
    OrderIntent,
    RiskLimits,
    run_paper_execution,
)


def test_service_builds_reconciliation_without_writing():
    report = run_paper_execution(
        intent=OrderIntent(
            asset="BTC-USD",
            side="BUY",
            quantity=0.01,
            reference_price=50_000.0,
            strategy_id="test",
            evidence_id="evidence",
        ),
        account=AccountSnapshot(
            cash=10_000.0
        ),
        limits=RiskLimits(
            maximum_order_notional=(
                1_000.0
            ),
            maximum_asset_notional=(
                1_000.0
            ),
            maximum_gross_exposure=(
                1_000.0
            ),
        ),
        write_outputs=False,
    )

    assert report[
        "reconciliation"
    ][
        "success"
    ]

    assert (
        report["provenance"][
            "event_count"
        ]
        >= 5
    )

    assert (
        report["execution_id"]
        .startswith(
            "PAPER-EXEC-"
        )
    )


def test_rejected_order_also_reconciles():
    report = run_paper_execution(
        intent=OrderIntent(
            asset="BTC-USD",
            side="BUY",
            quantity=1.0,
            reference_price=50_000.0,
            strategy_id="test",
            evidence_id="evidence",
        ),
        account=AccountSnapshot(
            cash=10_000.0
        ),
        limits=RiskLimits(
            maximum_order_notional=(
                500.0
            )
        ),
        write_outputs=False,
    )

    assert not report["success"]

    assert report[
        "reconciliation"
    ][
        "success"
    ]

    assert (
        report["order"][
            "status"
        ]
        == "REJECTED"
    )
