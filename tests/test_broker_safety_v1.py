from __future__ import annotations

import pytest

from atlas.investment.brokers import (
    BrokerCapabilityError,
    BrokerExecutionModeError,
    BrokerOrderRequest,
    BrokerOrderType,
    BrokerSide,
    BrokerTimeInForce,
    BrokerValidationError,
    MockBrokerAdapter,
)


class RejectAllGate:
    def assert_broker_submission_allowed(self, *, paper_only: bool) -> None:
        raise BrokerExecutionModeError("Submission blocked by test gate")


def test_default_adapter_declares_no_live_capability() -> None:
    broker = MockBrokerAdapter()

    assert broker.capabilities.paper_only is True
    assert broker.capabilities.live_trading is False


def test_submission_calls_execution_mode_gate() -> None:
    broker = MockBrokerAdapter(execution_gate=RejectAllGate())
    request = BrokerOrderRequest(
        client_order_id="blocked",
        symbol="BTC-USD",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=1.0,
    )

    with pytest.raises(BrokerExecutionModeError):
        broker.submit_order(request)


def test_unsupported_stop_order_fails_explicitly() -> None:
    broker = MockBrokerAdapter()
    request = BrokerOrderRequest(
        client_order_id="unsupported",
        symbol="BTC-USD",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.STOP,
        quantity=1.0,
        time_in_force=BrokerTimeInForce.DAY,
        stop_price=10.0,
    )

    with pytest.raises(BrokerCapabilityError):
        broker.submit_order(request)


@pytest.mark.parametrize(
    "quantity,symbol,client_order_id",
    [
        (0.0, "BTC-USD", "bad-quantity"),
        (-1.0, "BTC-USD", "negative"),
        (1.0, "", "missing-symbol"),
        (1.0, "BTC-USD", ""),
    ],
)
def test_invalid_orders_fail_validation(
    quantity: float,
    symbol: str,
    client_order_id: str,
) -> None:
    broker = MockBrokerAdapter()
    request = BrokerOrderRequest(
        client_order_id=client_order_id,
        symbol=symbol,
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=quantity,
    )

    with pytest.raises(BrokerValidationError):
        broker.submit_order(request)


def test_no_credentials_or_live_fields_exist_on_mock_adapter() -> None:
    broker = MockBrokerAdapter()

    assert not hasattr(broker, "api_key")
    assert not hasattr(broker, "api_secret")
    assert not hasattr(broker, "live_endpoint")
