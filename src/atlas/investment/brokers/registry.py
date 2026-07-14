"""Broker adapter registry for Atlas G.18."""

from __future__ import annotations

from collections.abc import Callable

from .base import BrokerAdapter
from .errors import BrokerConfigurationError, BrokerNotFoundError


BrokerFactory = Callable[..., BrokerAdapter]


class BrokerRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, BrokerFactory] = {}

    def register(
        self,
        provider: str,
        factory: BrokerFactory,
        *,
        replace: bool = False,
    ) -> None:
        key = provider.strip().lower()
        if not key:
            raise BrokerConfigurationError("Broker provider name is required")
        if key in self._factories and not replace:
            raise BrokerConfigurationError(
                f"Broker provider is already registered: {provider}"
            )
        self._factories[key] = factory

    def unregister(self, provider: str) -> None:
        key = provider.strip().lower()
        if key not in self._factories:
            raise BrokerNotFoundError(f"Broker provider is not registered: {provider}")
        del self._factories[key]

    def create(self, provider: str, **kwargs) -> BrokerAdapter:
        key = provider.strip().lower()
        try:
            factory = self._factories[key]
        except KeyError as exc:
            raise BrokerNotFoundError(
                f"Broker provider is not registered: {provider}"
            ) from exc
        adapter = factory(**kwargs)
        if not isinstance(adapter, BrokerAdapter):
            raise BrokerConfigurationError(
                f"Factory for {provider} did not return BrokerAdapter"
            )
        return adapter

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))


DEFAULT_BROKER_PROVIDER = "mock"
default_registry = BrokerRegistry()


__all__ = [
    "BrokerFactory",
    "BrokerRegistry",
    "DEFAULT_BROKER_PROVIDER",
    "default_registry",
]
