"""Safety-contract tests for G.15 provider adapters."""

from __future__ import annotations

from pathlib import Path


PACKAGE = Path(
    "src/atlas/investment/"
    "market_data"
)


def test_coinbase_adapter_has_no_credentials():
    text = (
        PACKAGE
        / "coinbase.py"
    ).read_text(
        encoding="utf-8"
    )

    forbidden = [
        "api_key",
        "api_secret",
        "passphrase",
        "Authorization",
        "CB-ACCESS-",
        "private_key",
        "place_order",
        "send_order",
        "submit_order",
    ]

    for value in forbidden:
        assert value not in text


def test_network_provider_is_read_only():
    text = (
        PACKAGE
        / "coinbase.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "credentials_required=False"
        in text
    )

    assert (
        "network_required=True"
        in text
    )

    assert (
        "trades=False"
        in text
    )
