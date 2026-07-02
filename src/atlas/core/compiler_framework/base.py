"""Compiler framework primitives for Atlas.

These types define the future Compiler V2 framework without changing current
compiler behavior yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class CompilerContext:
    """Shared context passed through compiler execution."""

    profile_key: str
    profile_payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PassMetadata:
    """Static metadata describing a compiler pass."""

    name: str
    version: str = "1.0"
    dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class PassResult:
    """Result emitted after a compiler pass runs."""

    name: str
    success: bool
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    elapsed_ms: float | None = None


class CompilerPass(Protocol):
    """Protocol implemented by all Atlas compiler passes."""

    metadata: PassMetadata

    def run(self, css: Any, context: CompilerContext) -> Any:
        """Run this compiler pass and return updated CSS."""
        ...
