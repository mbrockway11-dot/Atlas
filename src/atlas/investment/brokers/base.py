"""Abstract provider-neutral broker adapter for Atlas G.18."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from .contracts import (
    BrokerAccountSnapshot,
    BrokerCapabilities,
    BrokerHealthStatus,
    BrokerOrderRequest,
    BrokerOrderResponse,
    BrokerPosition,
)


@runtime_checkable
class ExecutionModeGate(Protocol):
    def assert_broker_submission_allowed(self, *, paper_only: bool) -> None:
        """Raise when the current mode does not permit submission."""


class BrokerAdapter(ABC):
    """Canonical broker interface.

    Implementations must remain mocked or paper-only during G.18.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def capabilities(self) -> BrokerCapabilities:
        raise NotImplementedError

    @abstractmethod
    def get_account(self) -> BrokerAccountSnapshot:
        raise NotImplementedError

    @abstractmethod
    def get_positions(self) -> list[BrokerPosition]:
        raise NotImplementedError

    @abstractmethod
    def get_open_orders(self) -> list[BrokerOrderResponse]:
        raise NotImplementedError

    @abstractmethod
    def submit_order(self, request: BrokerOrderRequest) -> BrokerOrderResponse:
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, broker_order_id: str) -> BrokerOrderResponse:
        raise NotImplementedError

    @abstractmethod
    def replace_order(
        self,
        broker_order_id: str,
        request: BrokerOrderRequest,
    ) -> BrokerOrderResponse:
        raise NotImplementedError

    @abstractmethod
    def get_order(self, broker_order_id: str) -> BrokerOrderResponse:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> BrokerHealthStatus:
        raise NotImplementedError


__all__ = ["BrokerAdapter", "ExecutionModeGate"]
