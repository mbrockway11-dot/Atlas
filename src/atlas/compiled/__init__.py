"""Compiled analytical artifact layer for Atlas."""

from atlas.compiled.compiler_identity import (
    COMPILER_NAME,
    COMPILER_VERSION,
    CompilerIdentity,
    build_compiler_identity,
    current_git_commit,
)
from atlas.compiled.hashing import sha256_file
from atlas.compiled.identity_vector_artifact import (
    COMPILED_IDENTITY_VECTOR_SCHEMA,
    CompiledIdentityVectorArtifact,
)
from atlas.compiled.identity_vector_compiler import (
    compile_identity_vector_artifact,
    source_acf_path_for_profile,
)
from atlas.compiled.identity_vector_store import (
    DEFAULT_COMPILED_VECTOR_DIR,
    artifact_path_for_profile,
    compiled_artifact_is_current,
    load_compiled_identity_vector,
    save_compiled_identity_vector,
)

__all__ = [
    "COMPILED_IDENTITY_VECTOR_SCHEMA",
    "COMPILER_NAME",
    "COMPILER_VERSION",
    "CompiledIdentityVectorArtifact",
    "CompilerIdentity",
    "DEFAULT_COMPILED_VECTOR_DIR",
    "artifact_path_for_profile",
    "build_compiler_identity",
    "compile_identity_vector_artifact",
    "compiled_artifact_is_current",
    "current_git_commit",
    "load_compiled_identity_vector",
    "save_compiled_identity_vector",
    "sha256_file",
    "source_acf_path_for_profile",
]
