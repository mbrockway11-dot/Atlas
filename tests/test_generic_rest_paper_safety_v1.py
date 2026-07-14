from __future__ import annotations

import pytest

from atlas.investment.brokers import (
    BrokerConfigurationError,
    BrokerDuplicateOrderError,
    BrokerExecutionModeError,
    BrokerOrderRequest,
    BrokerOrderType,
    BrokerSide,
    FixtureRestTransport,
    GenericRestPaperAdapter,
    GenericRestPaperConfig,
    RestRateLimitError,
)


class RejectGate:
    def assert_broker_submission_allowed(self, *, paper_only: bool) -> None:
        raise BrokerExecutionModeError("blocked")


def make_response(client_order_id: str):
    return {
        "broker_order_id": "order-1",
        "client_order_id": client_order_id,
        "symbol": "BTC-USD",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity": 1,
        "filled_quantity": 0,
        "status": "ACCEPTED",
        "average_fill_price": None,
    }


def test_adapter_rejects_live_configuration() -> None:
    with pytest.raises(BrokerConfigurationError):
        GenericRestPaperAdapter(
            config=GenericRestPaperConfig(
                provider="unsafe",
                paper_only=False,
                live_execution=True,
            ),
            transport=FixtureRestTransport({}),
        )


def test_adapter_rejects_credential_requirement() -> None:
    with pytest.raises(BrokerConfigurationError):
        GenericRestPaperAdapter(
            config=GenericRestPaperConfig(
                provider="unsafe",
                credentials_required=True,
            ),
            transport=FixtureRestTransport({}),
        )


def test_execution_gate_is_required_for_submission() -> None:
    broker = GenericRestPaperAdapter(
        config=GenericRestPaperConfig(provider="fixture"),
        transport=FixtureRestTransport({}),
        execution_gate=RejectGate(),
    )

    with pytest.raises(BrokerExecutionModeError):
        broker.submit_order(
            BrokerOrderRequest(
                client_order_id="blocked",
                symbol="BTC-USD",
                side=BrokerSide.BUY,
                order_type=BrokerOrderType.MARKET,
                quantity=1,
            )
        )


def test_duplicate_client_order_id_is_rejected() -> None:
    transport = FixtureRestTransport(
        {
            ("POST", "/paper/orders"): [
                make_response("duplicate"),
                make_response("duplicate"),
            ]
        }
    )
    broker = GenericRestPaperAdapter(
        config=GenericRestPaperConfig(provider="fixture"),
        transport=transport,
    )
    request = BrokerOrderRequest(
        client_order_id="duplicate",
        symbol="BTC-USD",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=1,
    )

    broker.submit_order(request)

    with pytest.raises(BrokerDuplicateOrderError):
        broker.submit_order(request)


def test_rate_limit_retries_then_succeeds() -> None:
    transport = FixtureRestTransport(
        {
            ("GET", "/paper/account"): [
                {"__raise__": "rate_limit", "message": "retry"},
                {
                    "account_id": "paper",
                    "cash": 1000,
                    "equity": 1000,
                    "buying_power": 1000,
                },
            ]
        }
    )
    broker = GenericRestPaperAdapter(
        config=GenericRestPaperConfig(provider="fixture", max_retries=1),
        transport=transport,
    )

    account = broker.get_account()

    assert account.account_id == "paper"
    assert len(transport.requests) == 2


def test_rate_limit_exhaustion_fails_explicitly() -> None:
    transport = FixtureRestTransport(
        {
            ("GET", "/paper/account"): [
                {"__raise__": "rate_limit"},
                {"__raise__": "rate_limit"},
            ]
        }
    )
    broker = GenericRestPaperAdapter(
        config=GenericRestPaperConfig(provider="fixture", max_retries=1),
        transport=transport,
    )

    with pytest.raises(RestRateLimitError):
        broker.get_account()
