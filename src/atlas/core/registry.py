"""Atlas Core registries.

The node registry supports newer graph-oriented workflows. ``PluginRegistry``
is a compatibility registry for the immutable ResearchContext plugin kernel.
"""

from __future__ import annotations

from typing import Any, Iterable

from atlas.core.node import Node


class NodeRegistry:
    """Registry for node-oriented core workflows."""

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}

    def register(self, node: Node) -> None:
        if node.name in self.nodes:
            raise ValueError(f"Duplicate node registered: {node.name}")
        self.nodes[node.name] = node

    def get(self, name: str) -> Node:
        return self.nodes[name]

    def all(self) -> list[Node]:
        return list(self.nodes.values())

    def names(self) -> list[str]:
        return list(self.nodes.keys())


class PluginRegistry:
    """Backward-compatible registry for ResearchContext plugins.

    Plugins are expected to expose ``name``, ``order``, ``depends_on`` and an
    ``execute(context)`` method. Dependency order takes precedence over the
    numeric order field; numeric order and name provide deterministic ties.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, Any] = {}

    def register(self, plugin: Any) -> None:
        name = str(plugin.name)
        if name in self._plugins:
            raise ValueError(f"Duplicate plugin registered: {name}")
        self._plugins[name] = plugin

    def get(self, name: str) -> Any:
        return self._plugins[name]

    def all(self) -> list[Any]:
        return list(self._plugins.values())

    def names(self) -> list[str]:
        return list(self._plugins.keys())

    def ordered(self, *, enabled: Iterable[str] | None = None) -> list[Any]:
        active_names = (
            set(self._plugins)
            if enabled is None
            else {name for name in enabled if name in self._plugins}
        )

        visiting: set[str] = set()
        visited: set[str] = set()
        result: list[Any] = []

        def visit(name: str) -> None:
            if name in visited:
                return
            if name in visiting:
                raise ValueError(f"Circular plugin dependency detected at: {name}")
            if name not in self._plugins:
                raise ValueError(f"Unknown plugin dependency: {name}")

            visiting.add(name)
            plugin = self._plugins[name]
            dependencies = tuple(getattr(plugin, "depends_on", ()) or ())
            for dependency in sorted(
                dependencies,
                key=lambda item: (
                    getattr(self._plugins.get(item), "order", 0),
                    item,
                ),
            ):
                if dependency not in self._plugins:
                    raise ValueError(
                        f"Plugin {name} depends on unknown plugin: {dependency}"
                    )
                if dependency in active_names:
                    visit(dependency)

            visiting.remove(name)
            visited.add(name)
            result.append(plugin)

        for name in sorted(
            active_names,
            key=lambda item: (
                getattr(self._plugins[item], "order", 0),
                item,
            ),
        ):
            visit(name)

        return result


__all__ = ["NodeRegistry", "PluginRegistry"]
