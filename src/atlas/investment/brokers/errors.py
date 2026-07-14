"""Broker-specific errors for Atlas G.18."""


class BrokerError(RuntimeError):
    """Base broker abstraction error."""


class BrokerConfigurationError(BrokerError):
    """Broker configuration is invalid."""


class BrokerCapabilityError(BrokerError):
    """Requested operation is not supported by the adapter."""


class BrokerExecutionModeError(BrokerError):
    """Execution mode does not permit broker submission."""


class BrokerValidationError(BrokerError):
    """Broker request validation failed."""


class BrokerNotFoundError(BrokerError):
    """Broker order or provider was not found."""


class BrokerDuplicateOrderError(BrokerError):
    """Client order ID was already used."""


__all__ = [
    "BrokerError",
    "BrokerConfigurationError",
    "BrokerCapabilityError",
    "BrokerExecutionModeError",
    "BrokerValidationError",
    "BrokerNotFoundError",
    "BrokerDuplicateOrderError",
]
