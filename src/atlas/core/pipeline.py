"""Core Atlas pipeline execution."""

from __future__ import annotations

from atlas.core.context import ResearchContext
from atlas.core.registry import GLOBAL_PLUGIN_REGISTRY, AtlasPlugin, PluginRegistry


def run_core_pipeline(
    context: ResearchContext,
    *,
    registry: PluginRegistry | None = None,
    enabled: set[str] | None = None,
) -> ResearchContext:
    """Run plugins in dependency-safe order."""
    active_registry = registry or GLOBAL_PLUGIN_REGISTRY
    current = context

    for plugin in active_registry.ordered(enabled=enabled):
        try:
            current = plugin.execute(current)
        except Exception as exc:
            current = current.with_warning(
                f"Plugin {plugin.name} failed: {type(exc).__name__}: {exc}"
            )

    return current