from __future__ import annotations

import pytest

from atlas.investment.brokers import (
    BrokerDuplicateOrderError,
    BrokerOrderRequest,
    BrokerOrderStatus,
    BrokerOrderType,
    BrokerSide,
    BrokerTimeInForce,
    MockBrokerAdapter,
)


def request(client_order_id: str = "client-1") -> BrokerOrderRequest:
    return BrokerOrderRequest(
        client_order_id=client_order_id,
        symbol="ETH-USD",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.LIMIT,
        quantity=1.5,
        time_in_force=BrokerTimeInForce.GTC,
        limit_price=2_500.0,
    )


def test_mock_broker_submit_get_cancel_cycle() -> None:
    broker = MockBrokerAdapter()

    accepted = broker.submit_order(request())

    assert accepted.status == BrokerOrderStatus.ACCEPTED
    assert accepted.paper_only is True
    assert accepted.live_execution is False
    assert broker.get_order(accepted.broker_order_id) == accepted
    assert len(broker.get_open_orders()) == 1

    cancelled = broker.cancel_order(accepted.broker_order_id)

    assert cancelled.status == BrokerOrderStatus.CANCELLED
    assert broker.get_open_orders() == []


def test_mock_broker_replace_order() -> None:
    broker = MockBrokerAdapter()
    original = broker.submit_order(request("client-original"))

    replacement = broker.replace_order(
        original.broker_order_id,
        request("client-replacement"),
    )

    assert replacement.broker_order_id == original.broker_order_id
    assert replacement.client_order_id == "client-replacement"
    assert replacement.status == BrokerOrderStatus.REPLACED


def test_duplicate_client_order_id_rejected() -> None:
    broker = MockBrokerAdapter()
    broker.submit_order(request("duplicate"))

    with pytest.raises(BrokerDuplicateOrderError):
        broker.submit_order(request("duplicate"))


def test_account_health_and_positions_are_paper_only() -> None:
    broker = MockBrokerAdapter(starting_cash=25_000)

    account = broker.get_account()
    health = broker.health_check()

    assert account.cash == 25_000
    assert account.paper_only is True
    assert account.live_execution is False
    assert health.paper_only is True
    assert health.live_execution is False
    assert broker.get_positions() == []
