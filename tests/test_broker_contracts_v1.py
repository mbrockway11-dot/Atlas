from __future__ import annotations

from dataclasses import asdict

from atlas.investment.brokers import (
    BrokerCapabilities,
    BrokerOrderRequest,
    BrokerOrderType,
    BrokerSide,
    BrokerTimeInForce,
)


def test_broker_contracts_are_provider_neutral() -> None:
    capabilities = BrokerCapabilities(provider="example")
    request = BrokerOrderRequest(
        client_order_id="client-1",
        symbol="BTC-USD",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.LIMIT,
        quantity=0.25,
        time_in_force=BrokerTimeInForce.GTC,
        limit_price=50_000.0,
    )

    assert capabilities.provider == "example"
    assert capabilities.paper_only is True
    assert capabilities.live_trading is False

    payload = asdict(request)
    assert payload["symbol"] == "BTC-USD"
    assert payload["quantity"] == 0.25
    assert payload["limit_price"] == 50_000.0


def test_live_capability_defaults_false() -> None:
    capabilities = BrokerCapabilities(provider="safe-default")
    assert capabilities.paper_only is True
    assert capabilities.live_trading is False
