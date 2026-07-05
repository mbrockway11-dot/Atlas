"""Plugin registry and dependency ordering for Atlas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from atlas.core.context import ResearchContext


class AtlasPlugin(Protocol):
    """Protocol for registry-managed Atlas plugins."""

    name: str
    order: int
    depends_on: tuple[str, ...]

    def execute(self, context: ResearchContext) -> ResearchContext:
        """Execute plugin and return updated context."""


@dataclass
class PluginRegistry:
    """Registry for Atlas plugins."""

    _plugins: dict[str, AtlasPlugin] = field(default_factory=dict)

    def register(self, plugin: AtlasPlugin) -> None:
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin already registered: {plugin.name}")
        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> AtlasPlugin:
        return self._plugins[name]

    def names(self) -> list[str]:
        return sorted(self._plugins)

    def enabled_plugins(self, enabled: set[str] | None = None) -> list[AtlasPlugin]:
        if enabled is None:
            return list(self._plugins.values())
        return [plugin for name, plugin in self._plugins.items() if name in enabled]

    def ordered(self, enabled: set[str] | None = None) -> list[AtlasPlugin]:
        plugins = self.enabled_plugins(enabled)
        plugin_map = {plugin.name: plugin for plugin in plugins}

        ordered: list[AtlasPlugin] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(name: str) -> None:
            if name in visited:
                return
            if name in visiting:
                raise ValueError(f"Circular plugin dependency detected at: {name}")
            if name not in plugin_map:
                raise ValueError(f"Missing plugin dependency: {name}")

            visiting.add(name)
            plugin = plugin_map[name]

            for dependency in getattr(plugin, "depends_on", ()):
                if dependency in plugin_map:
                    visit(dependency)

            visiting.remove(name)
            visited.add(name)
            ordered.append(plugin)

        for plugin in sorted(plugins, key=lambda item: (item.order, item.name)):
            visit(plugin.name)

        return ordered


GLOBAL_PLUGIN_REGISTRY = PluginRegistry()


def register_plugin(plugin: AtlasPlugin) -> AtlasPlugin:
    """Register plugin in the global registry."""
    GLOBAL_PLUGIN_REGISTRY.register(plugin)
    return plugin
