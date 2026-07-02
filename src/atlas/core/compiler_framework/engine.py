"""Compiler engine for Atlas Compiler V2."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from atlas.core.compiler_framework.base import (
    CompilerContext,
    CompilerPass,
    PassResult,
)
from atlas.core.compiler_framework.dependencies import order_passes_by_dependency
from atlas.core.compiler_framework.registry import PassRegistry


@dataclass
class CompilerEngine:
    """Deterministic compiler-pass execution engine."""

    registry: PassRegistry = field(default_factory=PassRegistry)

    def register(self, compiler_pass: CompilerPass) -> None:
        """Register one compiler pass."""
        self.registry.register(compiler_pass)

    @property
    def passes(self) -> list[CompilerPass]:
        """Return registered compiler passes in dependency order."""
        return order_passes_by_dependency(self.registry.passes())

    def run(self, css: Any, context: CompilerContext) -> tuple[Any, list[PassResult]]:
        """Run registered passes in dependency order."""
        results: list[PassResult] = []

        try:
            ordered_passes = self.passes
        except ValueError as exc:
            return css, [
                PassResult(
                    name="compiler_engine",
                    success=False,
                    errors=(str(exc),),
                )
            ]

        for compiler_pass in ordered_passes:
            metadata = compiler_pass.metadata
            start = perf_counter()

            try:
                css = compiler_pass.run(css, context)
                elapsed_ms = (perf_counter() - start) * 1000
                results.append(
                    PassResult(
                        name=metadata.name,
                        success=True,
                        elapsed_ms=elapsed_ms,
                    )
                )
            except Exception as exc:  # pragma: no cover
                elapsed_ms = (perf_counter() - start) * 1000
                results.append(
                    PassResult(
                        name=metadata.name,
                        success=False,
                        errors=(str(exc),),
                        elapsed_ms=elapsed_ms,
                    )
                )

        return css, results
