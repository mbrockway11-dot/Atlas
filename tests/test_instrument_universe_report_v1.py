"""Tests for the instrument universe audit report."""

from __future__ import annotations

from atlas.investment.execution.instruments import (
    build_instrument_universe_report,
)


def test_universe_report_is_safe():
    report = (
        build_instrument_universe_report(
            write_output=False
        )
    )

    assert report["success"]

    assert (
        report["counts"][
            "paper_enabled"
        ]
        >= 20
    )

    assert not report[
        "contract"
    ][
        "direct_futures_enabled"
    ]

    assert not report[
        "contract"
    ][
        "margin_trading_enabled"
    ]

    assert not report[
        "contract"
    ][
        "live_execution_enabled"
    ]
