"""Atlas Core pipelines.

``Pipeline`` supports newer node-oriented execution planning.
``run_core_pipeline`` preserves the immutable ResearchContext plugin API used by
the kernel and legacy callers.
"""

from __future__ import annotations

from atlas.core.context import ResearchContext
from atlas.core.dependency_graph import resolve_execution_order
from atlas.core.node import Node
from atlas.core.registry import NodeRegistry, PluginRegistry


class Pipeline:
    """Execution planner for node-oriented workflows."""

    def __init__(self, registry: NodeRegistry) -> None:
        self.registry = registry

    def execution_order(self) -> list[Node]:
        return resolve_execution_order(self.registry.all())


def run_core_pipeline(
    context: ResearchContext,
    *,
    registry: PluginRegistry,
    enabled: set[str] | None = None,
) -> ResearchContext:
    """Execute ResearchContext plugins in dependency order.

    Plugin failures are captured as warnings so one unavailable plugin does not
    prevent independent plugins from completing.
    """
    current = context
    for plugin in registry.ordered(enabled=enabled):
        try:
            current = plugin.execute(current)
        except Exception as error:  # compatibility boundary by design
            current = current.with_warning(
                f"Plugin {plugin.name} failed: "
                f"{type(error).__name__}: {error}"
            )
    return current


__all__ = ["Pipeline", "run_core_pipeline"]
