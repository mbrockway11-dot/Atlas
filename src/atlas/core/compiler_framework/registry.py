"""Pass registry for Atlas Compiler V2."""

from __future__ import annotations

from dataclasses import dataclass, field

from atlas.core.compiler_framework.base import CompilerPass


@dataclass
class PassRegistry:
    """Registry for compiler passes keyed by pass name."""

    _passes: dict[str, CompilerPass] = field(default_factory=dict)

    def register(self, compiler_pass: CompilerPass) -> None:
        """Register one compiler pass by metadata name."""
        name = compiler_pass.metadata.name

        if name in self._passes:
            raise ValueError(f"Duplicate compiler pass registered: {name}")

        self._passes[name] = compiler_pass

    def get(self, name: str) -> CompilerPass:
        """Return a compiler pass by name."""
        return self._passes[name]

    def names(self) -> list[str]:
        """Return registered pass names in registration order."""
        return list(self._passes.keys())

    def passes(self) -> list[CompilerPass]:
        """Return registered passes in registration order."""
        return list(self._passes.values())

    def __contains__(self, name: str) -> bool:
        """Return whether a pass name is registered."""
        return name in self._passes

    def __len__(self) -> int:
        """Return registered pass count."""
        return len(self._passes)
