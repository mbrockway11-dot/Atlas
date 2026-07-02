"""Public Atlas compiler entrypoint.

This module intentionally delegates to the modular compiler implementation in
atlas.core.compiler_passes.compiler.

Keep this file thin so external imports remain stable:

    from atlas.core.compiler import compile_profile
"""

from __future__ import annotations

from atlas.core.compiler_passes.compiler import (
    CORE_COMPILER_VERSION,
    build_compiler_metrics,
    compile_profile,
    compile_profile_payload,
    has_cipher_data,
    has_kamea_data,
    has_temporal_data,
)

__all__ = [
    "CORE_COMPILER_VERSION",
    "build_compiler_metrics",
    "compile_profile",
    "compile_profile_payload",
    "has_cipher_data",
    "has_kamea_data",
    "has_temporal_data",
]
