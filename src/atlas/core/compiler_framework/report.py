"""Compilation report objects for Atlas Compiler V2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas.core.compiler_framework.base import PassResult


@dataclass(frozen=True)
class CompilationReport:
    """Execution report for one compiler run."""

    compiler_version: str
    success: bool
    pass_results: tuple[PassResult, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    total_elapsed_ms: float

    @property
    def pass_count(self) -> int:
        """Return number of executed passes."""
        return len(self.pass_results)

    @property
    def passes(self) -> tuple[str, ...]:
        """Return executed pass names."""
        return tuple(result.name for result in self.pass_results)

    def to_dict(self) -> dict[str, Any]:
        """Return serializable report payload."""
        return {
            "compiler_version": self.compiler_version,
            "success": self.success,
            "pass_count": self.pass_count,
            "passes": list(self.passes),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "total_elapsed_ms": self.total_elapsed_ms,
            "pass_results": [
                {
                    "name": result.name,
                    "success": result.success,
                    "warnings": list(result.warnings),
                    "errors": list(result.errors),
                    "elapsed_ms": result.elapsed_ms,
                }
                for result in self.pass_results
            ],
        }


def build_compilation_report(
    *,
    compiler_version: str,
    pass_results: list[PassResult],
    total_elapsed_ms: float,
) -> CompilationReport:
    """Build a compilation report from pass results."""
    warnings = tuple(
        warning
        for result in pass_results
        for warning in result.warnings
    )
    errors = tuple(
        error
        for result in pass_results
        for error in result.errors
    )

    return CompilationReport(
        compiler_version=compiler_version,
        success=not errors and all(result.success for result in pass_results),
        pass_results=tuple(pass_results),
        warnings=warnings,
        errors=errors,
        total_elapsed_ms=total_elapsed_ms,
    )
