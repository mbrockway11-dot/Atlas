"""Tests for the canonical Atlas instrument registry."""

from __future__ import annotations

import pytest

from atlas.investment.execution.instruments import (
    INSTRUMENT_REGISTRY,
    get_instrument,
    list_instruments,
    normalize_symbol,
    require_paper_instrument,
    validate_instrument_registry,
)


def test_registry_is_structurally_valid():
    assert (
        validate_instrument_registry()
        == []
    )


def test_required_diversified_assets_exist():
    required = {
        "BTC-USD",
        "ETH-USD",
        "SOL-USD",
        "XRP-USD",
        "LINK-USD",
        "AVAX-USD",
        "GLD",
        "SLV",
        "USO",
        "BNO",
        "XLE",
        "SPY",
        "QQQ",
        "IWM",
        "TLT",
        "IEF",
        "UUP",
    }

    assert required.issubset(
        INSTRUMENT_REGISTRY
    )


def test_aliases_normalize():
    assert (
        normalize_symbol("btc")
        == "BTC-USD"
    )

    assert (
        normalize_symbol("gold")
        == "GLD"
    )

    assert (
        normalize_symbol("oil")
        == "USO"
    )


def test_direct_futures_are_disabled():
    for symbol in (
        "GC=F",
        "CL=F",
        "NG=F",
    ):
        instrument = get_instrument(
            symbol
        )

        assert (
            instrument is not None
        )

        assert not (
            instrument.paper_enabled
        )

        with pytest.raises(
            ValueError,
            match=(
                "PAPER_EXECUTION_DISABLED"
            ),
        ):
            require_paper_instrument(
                symbol
            )


def test_paper_universe_has_no_leveraged_contracts():
    for instrument in list_instruments(
        paper_enabled=True
    ):
        assert not (
            instrument.leveraged_contract
        )
