"""Tests for registry-aligned Atlas market sessions."""

from __future__ import annotations

from datetime import UTC, datetime

from atlas.investment.scheduling import (
    evaluate_instrument_session,
    evaluate_market_session,
    evaluate_symbol_sessions,
)


def test_continuous_session_is_open():
    status = evaluate_market_session(
        "CONTINUOUS",
        now=datetime(
            2026,
            7,
            11,
            12,
            0,
            tzinfo=UTC,
        ),
    )

    assert status.is_open
    assert status.reason == (
        "CONTINUOUS_SESSION"
    )


def test_always_session_is_open():
    status = evaluate_market_session(
        "ALWAYS",
        now=datetime(
            2026,
            7,
            11,
            12,
            0,
            tzinfo=UTC,
        ),
    )

    assert status.is_open
    assert status.reason == (
        "ALWAYS_AVAILABLE"
    )


def test_us_equities_open_during_rth():
    status = evaluate_market_session(
        "US_EQUITIES",
        now=datetime(
            2026,
            7,
            13,
            14,
            0,
            tzinfo=UTC,
        ),
    )

    assert status.is_open
    assert status.reason == (
        "SESSION_OPEN"
    )


def test_us_equities_closed_weekend():
    status = evaluate_market_session(
        "US_EQUITIES",
        now=datetime(
            2026,
            7,
            11,
            14,
            0,
            tzinfo=UTC,
        ),
    )

    assert not status.is_open
    assert status.reason == (
        "WEEKEND"
    )


def test_instrument_session_uses_registry():
    crypto = (
        evaluate_instrument_session(
            "BTC",
            now=datetime(
                2026,
                7,
                11,
                12,
                0,
                tzinfo=UTC,
            ),
        )
    )

    equity = (
        evaluate_instrument_session(
            "SPY",
            now=datetime(
                2026,
                7,
                13,
                14,
                0,
                tzinfo=UTC,
            ),
        )
    )

    assert crypto.session_name == (
        "CONTINUOUS"
    )

    assert equity.session_name == (
        "US_EQUITIES"
    )


def test_mixed_symbols_report_closed_equity():
    report = evaluate_symbol_sessions(
        [
            "BTC-USD",
            "SPY",
        ],
        now=datetime(
            2026,
            7,
            12,
            14,
            0,
            tzinfo=UTC,
        ),
    )

    assert report["any_open"]
    assert not report["all_open"]

    assert report[
        "open_symbols"
    ] == [
        "BTC-USD"
    ]

    assert report[
        "closed_symbols"
    ] == [
        "SPY"
    ]


def test_unknown_session_fails_closed():
    try:
        evaluate_market_session(
            "UNKNOWN"
        )

    except KeyError as error:
        assert (
            "UNKNOWN_MARKET_SESSION"
            in str(error)
        )

    else:
        raise AssertionError(
            "Expected unknown session failure"
        )
