"""Tests for Atlas provider-neutral HTTP transport helpers."""

from __future__ import annotations

from atlas.investment.market_data.http import (
    build_url,
)


def test_build_url_encodes_query():
    result = build_url(
        "https://example.test/data",
        query={
            "granularity": 3600,
            "symbol": "BTC-USD",
        },
    )

    assert result.startswith(
        "https://example.test/data?"
    )

    assert (
        "granularity=3600"
        in result
    )

    assert (
        "symbol=BTC-USD"
        in result
    )


def test_build_url_preserves_existing_query():
    result = build_url(
        "https://example.test/data?a=1",
        query={
            "b": 2,
        },
    )

    assert result == (
        "https://example.test/data?a=1&b=2"
    )
