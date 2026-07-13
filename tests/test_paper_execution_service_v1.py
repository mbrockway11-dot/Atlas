"""Integration tests for the complete Phase G paper execution slice."""

from __future__ import annotations

from atlas.investment.execution import (
    AccountSnapshot,
    OrderIntent,
    RiskLimits,
    run_paper_execution,
)


def test_approved_intent_updates_account():
    report = run_paper_execution(
        intent=OrderIntent(
            asset="BTC-USD",
            side="BUY",
            quantity=0.01,
            reference_price=50_000.0,
            strategy_id="engine-a",
            evidence_id="evidence-1",
        ),
        account=AccountSnapshot(
            cash=10_000.0
        ),
        limits=RiskLimits(
            maximum_order_notional=1_000.0,
            maximum_asset_notional=1_000.0,
            maximum_gross_exposure=1_000.0,
            maximum_leverage=1.0,
        ),
        write_outputs=False,
    )

    assert report["success"]
    assert (
        report["mode"]
        == "PAPER"
    )
    assert not report[
        "live_execution"
    ]
    assert (
        report["order"][
            "status"
        ]
        == "FILLED"
    )
    assert (
        "BTC-USD"
        in report[
            "account_after"
        ][
            "positions"
        ]
    )


def test_rejected_intent_does_not_change_account():
    account = AccountSnapshot(
        cash=1_000.0
    )

    report = run_paper_execution(
        intent=OrderIntent(
            asset="BTC-USD",
            side="BUY",
            quantity=1.0,
            reference_price=50_000.0,
            strategy_id="engine-a",
            evidence_id="evidence-1",
        ),
        account=account,
        limits=RiskLimits(
            maximum_order_notional=500.0
        ),
        write_outputs=False,
    )

    assert not report["success"]
    assert (
        report["order"][
            "status"
        ]
        == "REJECTED"
    )

    assert (
        report["account_before"]
        == report[
            "account_after"
        ]
    )


def test_contract_is_paper_only():
    report = run_paper_execution(
        intent=OrderIntent(
            asset="TEST",
            side="BUY",
            quantity=1.0,
            reference_price=100.0,
            strategy_id="test",
            evidence_id="evidence",
        ),
        account=AccountSnapshot(
            cash=1_000.0
        ),
        write_outputs=False,
    )

    assert report[
        "contract"
    ][
        "paper_only"
    ]

    assert not report[
        "contract"
    ][
        "live_credentials_used"
    ]
