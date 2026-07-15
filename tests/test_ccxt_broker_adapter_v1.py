from __future__ import annotations

from typing import Any

import pytest

from atlas.investment.brokers import (
    BrokerCapabilityError,
    BrokerConfigurationError,
    BrokerDuplicateOrderError,
    BrokerHealthState,
    BrokerOrderRequest,
    BrokerOrderStatus,
    BrokerOrderType,
    BrokerSide,
    BrokerTimeInForce,
    CCXTBrokerAdapter,
    CCXTBrokerConfig,
    atlas_symbol_to_ccxt,
    ccxt_symbol_to_atlas,
)


class FakeCCXTExchange:
    id = "fake"

    def __init__(self) -> None:
        self.has = {
            "cancelOrder": True,
            "editOrder": True,
            "fetchPositions": True,
        }

        self.sandbox_enabled = False
        self.created_orders: list[dict[str, Any]] = []

    def set_sandbox_mode(
        self,
        enabled: bool,
    ) -> None:
        self.sandbox_enabled = enabled

    def load_markets(self):
        return {
            "SOL/USD": {},
        }

    def fetch_balance(self):
        return {
            "free": {
                "USD": 1000.0,
            },
            "used": {
                "USD": 200.0,
            },
            "total": {
                "USD": 1200.0,
                "SOL": 2.0,
            },
        }

    def fetch_positions(
        self,
        symbols=None,
        params=None,
    ):
        return [
            {
                "symbol": "SOL/USD",
                "contracts": 2.0,
                "side": "long",
                "entryPrice": 100.0,
                "markPrice": 110.0,
                "notional": 220.0,
                "unrealizedPnl": 20.0,
            }
        ]

    def fetch_open_orders(
        self,
        symbol=None,
        since=None,
        limit=None,
        params=None,
    ):
        return [
            {
                "id": "order-open",
                "clientOrderId": "client-open",
                "symbol": "SOL/USD",
                "side": "buy",
                "type": "limit",
                "amount": 1.0,
                "filled": 0.0,
                "status": "open",
                "average": None,
                "timestamp": 1_700_000_000_000,
            }
        ]

    def create_order(
        self,
        symbol,
        order_type,
        side,
        amount,
        price=None,
        params=None,
    ):
        self.created_orders.append({
            "symbol": symbol,
            "type": order_type,
            "side": side,
            "amount": amount,
            "price": price,
            "params": params,
        })

        return {
            "id": "order-created",
            "clientOrderId": params["clientOrderId"],
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "amount": amount,
            "filled": 0.0,
            "status": "open",
            "average": None,
            "timestamp": 1_700_000_000_000,
        }

    def cancel_order(
        self,
        order_id,
        symbol=None,
        params=None,
    ):
        return {
            "id": order_id,
            "clientOrderId": "client-1",
            "symbol": symbol or "SOL/USD",
            "side": "buy",
            "type": "limit",
            "amount": 1.0,
            "filled": 0.0,
            "status": "canceled",
            "average": None,
            "timestamp": 1_700_000_000_000,
        }

    def edit_order(
        self,
        order_id,
        symbol,
        order_type,
        side,
        amount,
        price=None,
        params=None,
    ):
        return {
            "id": order_id,
            "clientOrderId": params["clientOrderId"],
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "amount": amount,
            "filled": 0.0,
            "status": "replaced",
            "average": None,
            "timestamp": 1_700_000_000_000,
        }

    def fetch_order(
        self,
        order_id,
        symbol=None,
        params=None,
    ):
        return {
            "id": order_id,
            "clientOrderId": "client-1",
            "symbol": symbol or "SOL/USD",
            "side": "buy",
            "type": "limit",
            "amount": 1.0,
            "filled": 0.5,
            "status": "open",
            "average": 105.0,
            "timestamp": 1_700_000_000_000,
        }


def adapter() -> CCXTBrokerAdapter:
    return CCXTBrokerAdapter(
        config=CCXTBrokerConfig(
            exchange_id="fake",
            account_id="fake-sandbox",
        ),
        exchange=FakeCCXTExchange(),
    )


def test_ccxt_config_rejects_live_mode() -> None:
    with pytest.raises(
        BrokerConfigurationError
    ):
        CCXTBrokerConfig(
            exchange_id="kraken",
            sandbox=False,
        )

    with pytest.raises(
        BrokerConfigurationError
    ):
        CCXTBrokerConfig(
            exchange_id="kraken",
            live_execution=True,
        )


def test_symbol_translation() -> None:
    assert (
        atlas_symbol_to_ccxt(
            "SOL-USD"
        )
        == "SOL/USD"
    )

    assert (
        ccxt_symbol_to_atlas(
            "BTC/USDT"
        )
        == "BTC-USDT"
    )


def test_adapter_is_sandbox_and_paper_only() -> None:
    broker = adapter()

    assert broker._exchange.sandbox_enabled
    assert broker.capabilities.paper_only
    assert not broker.capabilities.live_trading


def test_account_positions_orders_and_health() -> None:
    broker = adapter()

    account = broker.get_account()
    positions = broker.get_positions()
    orders = broker.get_open_orders()
    health = broker.health_check()

    assert account.cash == 1000.0
    assert account.equity == 1200.0
    assert positions[0].symbol == "SOL-USD"
    assert positions[0].quantity == 2.0
    assert orders[0].status == (
        BrokerOrderStatus.ACCEPTED
    )
    assert health.state == (
        BrokerHealthState.HEALTHY
    )


def test_submit_normalizes_and_preserves_client_id() -> None:
    broker = adapter()

    response = broker.submit_order(
        BrokerOrderRequest(
            client_order_id="client-1",
            symbol="SOL-USD",
            side=BrokerSide.BUY,
            order_type=BrokerOrderType.LIMIT,
            quantity=0.5,
            time_in_force=BrokerTimeInForce.GTC,
            limit_price=100.0,
        )
    )

    assert response.broker_order_id == (
        "order-created"
    )

    assert response.client_order_id == (
        "client-1"
    )

    assert response.symbol == "SOL-USD"
    assert response.paper_only
    assert not response.live_execution

    sent = broker._exchange.created_orders[0]

    assert sent["symbol"] == "SOL/USD"
    assert sent["params"]["clientOrderId"] == (
        "client-1"
    )

    assert sent["params"]["atlasPaperOnly"]
    assert not sent["params"][
        "atlasLiveExecution"
    ]


def test_duplicate_client_order_id_is_rejected() -> None:
    broker = adapter()

    request = BrokerOrderRequest(
        client_order_id="duplicate",
        symbol="SOL-USD",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=0.1,
        time_in_force=BrokerTimeInForce.GTC,
    )

    broker.submit_order(request)

    with pytest.raises(
        BrokerDuplicateOrderError
    ):
        broker.submit_order(request)


def test_cancel_replace_and_fetch_order() -> None:
    broker = adapter()

    created = broker.submit_order(
        BrokerOrderRequest(
            client_order_id="client-1",
            symbol="SOL-USD",
            side=BrokerSide.BUY,
            order_type=BrokerOrderType.LIMIT,
            quantity=1.0,
            time_in_force=BrokerTimeInForce.GTC,
            limit_price=100.0,
        )
    )

    cancelled = broker.cancel_order(
        created.broker_order_id
    )

    replaced = broker.replace_order(
        created.broker_order_id,
        BrokerOrderRequest(
            client_order_id="client-2",
            symbol="SOL-USD",
            side=BrokerSide.BUY,
            order_type=BrokerOrderType.LIMIT,
            quantity=0.5,
            time_in_force=BrokerTimeInForce.GTC,
            limit_price=99.0,
        ),
    )

    fetched = broker.get_order(
        created.broker_order_id
    )

    assert cancelled.status == (
        BrokerOrderStatus.CANCELLED
    )

    assert replaced.status == (
        BrokerOrderStatus.REPLACED
    )

    assert fetched.filled_quantity == 0.5


def test_replace_rejected_when_exchange_lacks_edit() -> None:
    exchange = FakeCCXTExchange()
    exchange.has["editOrder"] = False

    broker = CCXTBrokerAdapter(
        config=CCXTBrokerConfig(
            exchange_id="fake",
        ),
        exchange=exchange,
    )

    with pytest.raises(
        BrokerCapabilityError
    ):
        broker.replace_order(
            "order-1",
            BrokerOrderRequest(
                client_order_id="replacement",
                symbol="SOL-USD",
                side=BrokerSide.BUY,
                order_type=BrokerOrderType.LIMIT,
                quantity=1.0,
                time_in_force=BrokerTimeInForce.GTC,
                limit_price=100.0,
            ),
        )
