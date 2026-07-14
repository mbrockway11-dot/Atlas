"""Capability validation for provider-neutral broker adapters."""

from __future__ import annotations

from .contracts import (
    BrokerCapabilities,
    BrokerOrderRequest,
    BrokerOrderType,
)
from .errors import BrokerCapabilityError


def validate_order_capabilities(
    request: BrokerOrderRequest,
    capabilities: BrokerCapabilities,
) -> None:
    support_map = {
        BrokerOrderType.MARKET: capabilities.supports_market_orders,
        BrokerOrderType.LIMIT: capabilities.supports_limit_orders,
        BrokerOrderType.STOP: capabilities.supports_stop_orders,
        BrokerOrderType.STOP_LIMIT: capabilities.supports_stop_limit_orders,
    }

    if not support_map[request.order_type]:
        raise BrokerCapabilityError(
            f"{capabilities.provider} does not support {request.order_type.value} orders"
        )

    if request.time_in_force.value not in capabilities.supported_time_in_force:
        raise BrokerCapabilityError(
            f"{capabilities.provider} does not support "
            f"time_in_force={request.time_in_force.value}"
        )

    if request.quantity % 1 and not capabilities.supports_fractional_quantity:
        raise BrokerCapabilityError(
            f"{capabilities.provider} does not support fractional quantity"
        )


__all__ = ["validate_order_capabilities"]
