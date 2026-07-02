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


@dataclass
class CompilerEngine:
    """Deterministic compiler-pass execution engine."""

    passes: list[CompilerPass] = field(default_factory=list)

    def register(self, compiler_pass: CompilerPass) -> None:
        """Register one compiler pass."""
        self.passes.append(compiler_pass)

    def run(self, css: Any, context: CompilerContext) -> tuple[Any, list[PassResult]]:
        """Run registered passes in order."""
        results: list[PassResult] = []
        completed: set[str] = set()

        for compiler_pass in self.passes:
            metadata = compiler_pass.metadata

            missing = [
                dependency
                for dependency in metadata.dependencies
                if dependency not in completed
            ]

            if missing:
                results.append(
                    PassResult(
                        name=metadata.name,
                        success=False,
                        errors=(
                            f"Missing dependencies: {', '.join(missing)}",
                        ),
                    )
                )
                continue

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
                completed.add(metadata.name)
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
