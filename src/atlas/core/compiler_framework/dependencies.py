"""Dependency ordering for Atlas compiler passes."""

from __future__ import annotations

from atlas.core.compiler_framework.base import CompilerPass


def order_passes_by_dependency(
    compiler_passes: list[CompilerPass],
) -> list[CompilerPass]:
    """Return compiler passes ordered by declared dependencies.

    Raises:
        ValueError: If a dependency is missing or a cycle is detected.
    """
    by_name = {compiler_pass.metadata.name: compiler_pass for compiler_pass in compiler_passes}

    ordered: list[CompilerPass] = []
    temporary: set[str] = set()
    permanent: set[str] = set()

    def visit(name: str) -> None:
        if name in permanent:
            return

        if name in temporary:
            raise ValueError(f"Compiler pass dependency cycle detected at: {name}")

        if name not in by_name:
            raise ValueError(f"Missing compiler pass dependency: {name}")

        temporary.add(name)

        compiler_pass = by_name[name]
        for dependency in compiler_pass.metadata.dependencies:
            visit(dependency)

        temporary.remove(name)
        permanent.add(name)
        ordered.append(compiler_pass)

    for compiler_pass in compiler_passes:
        visit(compiler_pass.metadata.name)

    return ordered
