"""Tests for conservative Atlas futures-session controls."""

from __future__ import annotations

from datetime import UTC, datetime

from atlas.investment.scheduling import (
    evaluate_market_session,
)


def test_futures_closed_saturday():
    status = evaluate_market_session(
        "FUTURES",
        now=datetime(
            2026,
            7,
            11,
            16,
            0,
            tzinfo=UTC,
        ),
    )

    assert not status.is_open
    assert status.reason == (
        "SATURDAY_CLOSED"
    )
    assert status.approximate


def test_futures_open_monday_daytime():
    status = evaluate_market_session(
        "FUTURES",
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


def test_futures_daily_maintenance_closed():
    status = evaluate_market_session(
        "FUTURES",
        now=datetime(
            2026,
            7,
            15,
            21,
            30,
            tzinfo=UTC,
        ),
    )

    assert not status.is_open
    assert status.reason == (
        "DAILY_MAINTENANCE"
    )


def test_futures_sunday_before_open():
    status = evaluate_market_session(
        "FUTURES",
        now=datetime(
            2026,
            7,
            12,
            18,
            0,
            tzinfo=UTC,
        ),
    )

    assert not status.is_open
    assert status.reason == (
        "SUNDAY_BEFORE_OPEN"
    )
