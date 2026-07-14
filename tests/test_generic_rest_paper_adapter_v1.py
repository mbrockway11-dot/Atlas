from __future__ import annotations

from atlas.investment.brokers import (
    BrokerOrderRequest,
    BrokerOrderStatus,
    BrokerOrderType,
    BrokerSide,
    BrokerTimeInForce,
    FixtureRestTransport,
    GenericRestPaperAdapter,
    GenericRestPaperConfig,
)


def adapter_with(fixtures):
    return GenericRestPaperAdapter(
        config=GenericRestPaperConfig(provider="fixture-paper"),
        transport=FixtureRestTransport(fixtures),
    )


def test_account_positions_and_health_are_normalized() -> None:
    broker = adapter_with(
        {
            ("GET", "/paper/account"): {
                "account_id": "paper-1",
                "currency": "USD",
                "cash": 1000,
                "equity": 1250,
                "buying_power": 1000,
                "gross_exposure": 250,
                "net_exposure": 250,
            },
            ("GET", "/paper/positions"): {
                "positions": [
                    {
                        "symbol": "btc/usd",
                        "quantity": 0.01,
                        "average_price": 50000,
                        "market_value": 600,
                    }
                ]
            },
            ("GET", "/paper/health"): {
                "state": "HEALTHY",
                "message": "fixture ok",
                "latency_ms": 2,
            },
        }
    )

    account = broker.get_account()
    positions = broker.get_positions()
    health = broker.health_check()

    assert account.paper_only is True
    assert account.live_execution is False
    assert positions[0].symbol == "BTC-USD"
    assert health.paper_only is True
    assert health.live_execution is False


def test_submit_order_translates_and_normalizes() -> None:
    transport = FixtureRestTransport(
        {
            ("POST", "/paper/orders"): {
                "broker_order_id": "paper-order-1",
                "client_order_id": "client-1",
                "symbol": "eth/usd",
                "side": "buy",
                "order_type": "limit",
                "quantity": 1.5,
                "filled_quantity": 0,
                "status": "open",
                "average_fill_price": None,
                "submitted_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            }
        }
    )
    broker = GenericRestPaperAdapter(
        config=GenericRestPaperConfig(provider="fixture-paper"),
        transport=transport,
    )

    response = broker.submit_order(
        BrokerOrderRequest(
            client_order_id="client-1",
            symbol="eth/usd",
            side=BrokerSide.BUY,
            order_type=BrokerOrderType.LIMIT,
            quantity=1.5,
            time_in_force=BrokerTimeInForce.GTC,
            limit_price=2500,
        )
    )

    assert response.status == BrokerOrderStatus.ACCEPTED
    assert response.symbol == "ETH-USD"
    assert response.paper_only is True
    assert response.live_execution is False

    sent = transport.requests[0]
    assert sent["headers"]["Idempotency-Key"] == "client-1"
    assert sent["json_body"]["paper_only"] is True
    assert sent["json_body"]["live_execution"] is False


def test_cancel_replace_and_get_order() -> None:
    broker = adapter_with(
        {
            ("POST", "/paper/orders/order-1/cancel"): {
                "broker_order_id": "order-1",
                "client_order_id": "client-1",
                "symbol": "BTC-USD",
                "side": "BUY",
                "order_type": "MARKET",
                "quantity": 1,
                "filled_quantity": 0,
                "status": "CANCELLED",
                "average_fill_price": None,
            },
            ("PUT", "/paper/orders/order-1"): {
                "broker_order_id": "order-1",
                "client_order_id": "client-2",
                "symbol": "BTC-USD",
                "side": "BUY",
                "order_type": "LIMIT",
                "quantity": 2,
                "filled_quantity": 0,
                "status": "REPLACED",
                "average_fill_price": None,
            },
            ("GET", "/paper/orders/order-1"): {
                "broker_order_id": "order-1",
                "client_order_id": "client-2",
                "symbol": "BTC-USD",
                "side": "BUY",
                "order_type": "LIMIT",
                "quantity": 2,
                "filled_quantity": 0,
                "status": "REPLACED",
                "average_fill_price": None,
            },
        }
    )

    cancelled = broker.cancel_order("order-1")
    replaced = broker.replace_order(
        "order-1",
        BrokerOrderRequest(
            client_order_id="client-2",
            symbol="BTC-USD",
            side=BrokerSide.BUY,
            order_type=BrokerOrderType.LIMIT,
            quantity=2,
            limit_price=50000,
        ),
    )
    fetched = broker.get_order("order-1")

    assert cancelled.status == BrokerOrderStatus.CANCELLED
    assert replaced.status == BrokerOrderStatus.REPLACED
    assert fetched.client_order_id == "client-2"
