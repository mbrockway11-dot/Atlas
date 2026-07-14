from __future__ import annotations

import pytest

from atlas.investment.brokers import (
    BrokerConfigurationError,
    BrokerNotFoundError,
    BrokerRegistry,
    MockBrokerAdapter,
)


def test_registry_creates_mock_adapter() -> None:
    registry = BrokerRegistry()
    registry.register("mock", MockBrokerAdapter)

    adapter = registry.create("mock")

    assert isinstance(adapter, MockBrokerAdapter)
    assert adapter.provider_name == "mock"
    assert registry.names() == ("mock",)


def test_registry_rejects_duplicate_provider() -> None:
    registry = BrokerRegistry()
    registry.register("mock", MockBrokerAdapter)

    with pytest.raises(BrokerConfigurationError):
        registry.register("mock", MockBrokerAdapter)


def test_registry_rejects_unknown_provider() -> None:
    registry = BrokerRegistry()

    with pytest.raises(BrokerNotFoundError):
        registry.create("missing")
