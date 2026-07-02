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
from atlas.core.compiler_framework.report import (
    CompilationReport,
    build_compilation_report,
)

__all__ = [
    "CompilationReport",
    "CompilerContext",
    "CompilerEngine",
    "CompilerPass",
    "PassMetadata",
    "PassRegistry",
    "PassResult",
    "build_compilation_report",
    "order_passes_by_dependency",
]
