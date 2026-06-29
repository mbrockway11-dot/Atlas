"""Default Atlas plugin registry."""

from __future__ import annotations

from atlas.core.registry import PluginRegistry
from atlas.plugins.identity import IdentityCorePlugin
from atlas.plugins.intelligence import IntelligenceCorePlugin
from atlas.plugins.statistics import StatisticsCorePlugin
from atlas.plugins.validation import ValidationCorePlugin


def build_default_registry() -> PluginRegistry:
    """Build default Atlas core plugin registry."""
    registry = PluginRegistry()
    registry.register(IdentityCorePlugin())
    registry.register(ValidationCorePlugin())
    registry.register(StatisticsCorePlugin())
    registry.register(IntelligenceCorePlugin())
    return registry


def default_enabled_plugins() -> set[str]:
    """Return default enabled plugin names."""
    return {
        "identity",
        "validation",
        "statistics",
        "intelligence",
    }