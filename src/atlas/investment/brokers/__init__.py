"""Atlas broker abstraction package."""

from .base import BrokerAdapter, ExecutionModeGate
from .capabilities import validate_order_capabilities
from .contracts import (
    BrokerAccountSnapshot,
    BrokerCapabilities,
    BrokerExecutionReport,
    BrokerHealthState,
    BrokerHealthStatus,
    BrokerOrderRequest,
    BrokerOrderResponse,
    BrokerOrderStatus,
    BrokerOrderType,
    BrokerPosition,
    BrokerSide,
    BrokerTimeInForce,
)
from .errors import (
    BrokerCapabilityError,
    BrokerConfigurationError,
    BrokerDuplicateOrderError,
    BrokerError,
    BrokerExecutionModeError,
    BrokerNotFoundError,
    BrokerValidationError,
)
from .fixtures import FixtureRestTransport
from .generic_rest_paper import (
    GenericRestPaperAdapter,
    GenericRestPaperConfig,
    RestAuthenticationError,
    RestRateLimitError,
    RestServerError,
    RestTransport,
    RestTransportError,
    normalize_order_status,
    normalize_order_type,
    normalize_side,
    normalize_symbol,
)
from .mock import MockBrokerAdapter, PaperOnlyExecutionGate
from .registry import (
    DEFAULT_BROKER_PROVIDER,
    BrokerRegistry,
    default_registry,
)

if DEFAULT_BROKER_PROVIDER not in default_registry.names():
    default_registry.register(DEFAULT_BROKER_PROVIDER, MockBrokerAdapter)

__all__ = [
    "BrokerAccountSnapshot",
    "BrokerAdapter",
    "BrokerCapabilities",
    "BrokerCapabilityError",
    "BrokerConfigurationError",
    "BrokerDuplicateOrderError",
    "BrokerError",
    "BrokerExecutionModeError",
    "BrokerExecutionReport",
    "BrokerHealthState",
    "BrokerHealthStatus",
    "BrokerNotFoundError",
    "BrokerOrderRequest",
    "BrokerOrderResponse",
    "BrokerOrderStatus",
    "BrokerOrderType",
    "BrokerPosition",
    "BrokerRegistry",
    "BrokerSide",
    "BrokerTimeInForce",
    "BrokerValidationError",
    "DEFAULT_BROKER_PROVIDER",
    "ExecutionModeGate",
    "FixtureRestTransport",
    "GenericRestPaperAdapter",
    "GenericRestPaperConfig",
    "MockBrokerAdapter",
    "PaperOnlyExecutionGate",
    "RestAuthenticationError",
    "RestRateLimitError",
    "RestServerError",
    "RestTransport",
    "RestTransportError",
    "default_registry",
    "normalize_order_status",
    "normalize_order_type",
    "normalize_side",
    "normalize_symbol",
    "validate_order_capabilities",
]
