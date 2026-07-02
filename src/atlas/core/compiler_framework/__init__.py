"""Atlas compiler framework."""

from atlas.core.compiler_framework.base import (
    CompilerContext,
    CompilerPass,
    PassMetadata,
    PassResult,
)
from atlas.core.compiler_framework.dependencies import order_passes_by_dependency
from atlas.core.compiler_framework.engine import CompilerEngine
from atlas.core.compiler_framework.registry import PassRegistry

__all__ = [
    "CompilerContext",
    "CompilerEngine",
    "CompilerPass",
    "PassMetadata",
    "PassRegistry",
    "PassResult",
    "order_passes_by_dependency",
]
