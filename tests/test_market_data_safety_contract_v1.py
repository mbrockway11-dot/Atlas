"""Static safety tests for the G.11 market-data layer."""

from __future__ import annotations

from pathlib import Path


PACKAGE = Path(
    "src/atlas/investment/"
    "market_data"
)


def test_market_data_layer_has_no_broker_calls():
    text = "\n".join(
        path.read_text(
            encoding="utf-8"
        )
        for path
        in PACKAGE.glob("*.py")
    )

    forbidden = [
        "run_paper_execution",
        "PaperBroker(",
        ".submit(",
        "send_order",
        "place_order",
        "api_secret",
        "private_key",
        "live_execution=True",
    ]

    for value in forbidden:
        assert value not in text


def test_static_provider_requires_no_credentials():
    text = (
        PACKAGE
        / "providers.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "credentials_required=False"
        in text
    )

    assert (
        "network_required=False"
        in text
    )
