"""Deterministic paper-only mock broker adapter for Atlas G.18."""

from __future__ import annotations

import itertools
from dataclasses import replace
from datetime import datetime, timezone

from .base import BrokerAdapter, ExecutionModeGate
from .capabilities import validate_order_capabilities
from .contracts import (
    BrokerAccountSnapshot,
    BrokerCapabilities,
    BrokerHealthState,
    BrokerHealthStatus,
    BrokerOrderRequest,
    BrokerOrderResponse,
    BrokerOrderStatus,
    BrokerPosition,
)
from .errors import (
    BrokerCapabilityError,
    BrokerDuplicateOrderError,
    BrokerExecutionModeError,
    BrokerNotFoundError,
    BrokerValidationError,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PaperOnlyExecutionGate:
    """Default G.18 gate. Only paper submissions are allowed."""

    def assert_broker_submission_allowed(self, *, paper_only: bool) -> None:
        if not paper_only:
            raise BrokerExecutionModeError("Live broker submission is disabled")


class MockBrokerAdapter(BrokerAdapter):
    def __init__(
        self,
        *,
        account_id: str = "mock-paper-account",
        starting_cash: float = 100_000.0,
        execution_gate: ExecutionModeGate | None = None,
    ) -> None:
        if starting_cash < 0:
            raise BrokerValidationError("starting_cash cannot be negative")

        self._account_id = account_id
        self._cash = float(starting_cash)
        self._orders: dict[str, BrokerOrderResponse] = {}
        self._client_order_ids: set[str] = set()
        self._positions: dict[str, BrokerPosition] = {}
        self._counter = itertools.count(1)
        self._execution_gate = execution_gate or PaperOnlyExecutionGate()
        self._capabilities = BrokerCapabilities(
            provider="mock",
            paper_only=True,
            live_trading=False,
            supports_market_orders=True,
            supports_limit_orders=True,
            supports_stop_orders=False,
            supports_stop_limit_orders=False,
            supports_cancel=True,
            supports_replace=True,
            supports_fractional_quantity=True,
            supports_shorting=False,
            supported_asset_classes=("GENERIC", "CRYPTO", "EQUITY"),
        )

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def capabilities(self) -> BrokerCapabilities:
        return self._capabilities

    def get_account(self) -> BrokerAccountSnapshot:
        gross = sum(abs(position.market_value) for position in self._positions.values())
        net = sum(position.market_value for position in self._positions.values())
        return BrokerAccountSnapshot(
            account_id=self._account_id,
            currency="USD",
            cash=self._cash,
            equity=self._cash + net,
            buying_power=self._cash,
            gross_exposure=gross,
            net_exposure=net,
            paper_only=True,
            live_execution=False,
        )

    def get_positions(self) -> list[BrokerPosition]:
        return [self._positions[key] for key in sorted(self._positions)]

    def get_open_orders(self) -> list[BrokerOrderResponse]:
        open_states = {
            BrokerOrderStatus.NEW,
            BrokerOrderStatus.ACCEPTED,
            BrokerOrderStatus.PARTIALLY_FILLED,
        }
        return [
            order
            for order in self._orders.values()
            if order.status in open_states
        ]

    def submit_order(self, request: BrokerOrderRequest) -> BrokerOrderResponse:
        self._execution_gate.assert_broker_submission_allowed(paper_only=True)
        self._validate_request(request)
        validate_order_capabilities(request, self.capabilities)

        if request.client_order_id in self._client_order_ids:
            raise BrokerDuplicateOrderError(
                f"Duplicate client_order_id: {request.client_order_id}"
            )

        broker_order_id = f"mock-{next(self._counter):08d}"
        timestamp = utc_now()
        response = BrokerOrderResponse(
            broker_order_id=broker_order_id,
            client_order_id=request.client_order_id,
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            filled_quantity=0.0,
            status=BrokerOrderStatus.ACCEPTED,
            average_fill_price=None,
            submitted_at=timestamp,
            updated_at=timestamp,
            paper_only=True,
            live_execution=False,
            raw={"provider": "mock"},
        )
        self._orders[broker_order_id] = response
        self._client_order_ids.add(request.client_order_id)
        return response

    def cancel_order(self, broker_order_id: str) -> BrokerOrderResponse:
        if not self.capabilities.supports_cancel:
            raise BrokerCapabilityError("Cancel is not supported")
        order = self.get_order(broker_order_id)
        if order.status in {
            BrokerOrderStatus.FILLED,
            BrokerOrderStatus.CANCELLED,
            BrokerOrderStatus.REJECTED,
            BrokerOrderStatus.EXPIRED,
        }:
            raise BrokerValidationError(
                f"Order cannot be cancelled from {order.status.value}"
            )
        updated = replace(
            order,
            status=BrokerOrderStatus.CANCELLED,
            updated_at=utc_now(),
        )
        self._orders[broker_order_id] = updated
        return updated

    def replace_order(
        self,
        broker_order_id: str,
        request: BrokerOrderRequest,
    ) -> BrokerOrderResponse:
        if not self.capabilities.supports_replace:
            raise BrokerCapabilityError("Replace is not supported")
        current = self.get_order(broker_order_id)
        if current.status not in {
            BrokerOrderStatus.NEW,
            BrokerOrderStatus.ACCEPTED,
            BrokerOrderStatus.PARTIALLY_FILLED,
        }:
            raise BrokerValidationError(
                f"Order cannot be replaced from {current.status.value}"
            )

        self._execution_gate.assert_broker_submission_allowed(paper_only=True)
        self._validate_request(request)
        validate_order_capabilities(request, self.capabilities)

        if (
            request.client_order_id in self._client_order_ids
            and request.client_order_id != current.client_order_id
        ):
            raise BrokerDuplicateOrderError(
                f"Duplicate client_order_id: {request.client_order_id}"
            )

        updated = BrokerOrderResponse(
            broker_order_id=current.broker_order_id,
            client_order_id=request.client_order_id,
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            filled_quantity=current.filled_quantity,
            status=BrokerOrderStatus.REPLACED,
            average_fill_price=current.average_fill_price,
            submitted_at=current.submitted_at,
            updated_at=utc_now(),
            paper_only=True,
            live_execution=False,
            raw={"provider": "mock", "replaced": True},
        )
        self._orders[broker_order_id] = updated
        self._client_order_ids.add(request.client_order_id)
        return updated

    def get_order(self, broker_order_id: str) -> BrokerOrderResponse:
        try:
            return self._orders[broker_order_id]
        except KeyError as exc:
            raise BrokerNotFoundError(
                f"Broker order not found: {broker_order_id}"
            ) from exc

    def health_check(self) -> BrokerHealthStatus:
        return BrokerHealthStatus(
            provider=self.provider_name,
            state=BrokerHealthState.HEALTHY,
            checked_at=utc_now(),
            message="Deterministic in-memory paper broker",
            latency_ms=0,
            paper_only=True,
            live_execution=False,
        )

    @staticmethod
    def _validate_request(request: BrokerOrderRequest) -> None:
        if not request.client_order_id.strip():
            raise BrokerValidationError("client_order_id is required")
        if not request.symbol.strip():
            raise BrokerValidationError("symbol is required")
        if request.quantity <= 0:
            raise BrokerValidationError("quantity must be positive")
        if request.order_type.value in {"LIMIT", "STOP_LIMIT"}:
            if request.limit_price is None or request.limit_price <= 0:
                raise BrokerValidationError(
                    "Positive limit_price is required for limit orders"
                )
        if request.order_type.value in {"STOP", "STOP_LIMIT"}:
            if request.stop_price is None or request.stop_price <= 0:
                raise BrokerValidationError(
                    "Positive stop_price is required for stop orders"
                )


__all__ = ["MockBrokerAdapter", "PaperOnlyExecutionGate"]
