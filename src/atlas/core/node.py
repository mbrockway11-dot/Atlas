
"""Atlas Core node abstraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class NodeResult:
    name: str
    success: bool
    output_key: str | None = None
    output: Any = None
    error: str | None = None
    warnings: list[str] = field(default_factory=list)


class Node:
    """Base pipeline node."""

    name: str = "node"
    requires: list[str] = []
    provides: list[str] = []

    def execute(self, state: "AtlasState", context: "AtlasContext") -> NodeResult:
        raise NotImplementedError
