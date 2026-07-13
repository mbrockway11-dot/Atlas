"""Tests for extracting portfolio reference prices from market snapshots."""

from __future__ import annotations

import pytest

from atlas.investment.market_data import (
    reference_prices_from_snapshot,
)


def test_snapshot_prices_normalize_aliases():
    prices = (
        reference_prices_from_snapshot({
            "reference_prices": {
                "btc": 50_000.0,
                "gold": 300.0,
                "oil": 80.0,
            }
        })
    )

    assert prices == {
        "BTC-USD": 50_000.0,
        "GLD": 300.0,
        "USO": 80.0,
    }


def test_unknown_snapshot_symbol_fails():
    with pytest.raises(
        KeyError,
        match=(
            "UNREGISTERED_INSTRUMENT"
        ),
    ):
        reference_prices_from_snapshot({
            "reference_prices": {
                "UNKNOWN": 100.0,
            }
        })
