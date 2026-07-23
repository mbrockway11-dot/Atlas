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
from atlas.compiled.identity_vector_library_compiler import (
    EXPECTED_VECTOR_COUNT,
    LibraryCompilationResult,
    ProfileCompilationOutcome,
    compile_identity_vector_library,
    list_compilable_profile_keys,
    storage_reduction_ratio,
)
from atlas.compiled.identity_vector_store import (
    DEFAULT_COMPILED_VECTOR_DIR,
    artifact_path_for_profile,
    compiled_artifact_is_current,
    load_compiled_identity_vector,
    save_compiled_identity_vector,
)
from atlas.compiled.manifest import (
    COMPILED_MANIFEST_SCHEMA,
    DEFAULT_MANIFEST_PATH,
    CompilationManifest,
    build_compilation_manifest,
    save_compilation_manifest,
)

__all__ = [
    "COMPILED_IDENTITY_VECTOR_SCHEMA",
    "COMPILED_MANIFEST_SCHEMA",
    "COMPILER_NAME",
    "COMPILER_VERSION",
    "CompilationManifest",
    "CompiledIdentityVectorArtifact",
    "CompilerIdentity",
    "DEFAULT_COMPILED_VECTOR_DIR",
    "DEFAULT_MANIFEST_PATH",
    "EXPECTED_VECTOR_COUNT",
    "LibraryCompilationResult",
    "ProfileCompilationOutcome",
    "artifact_path_for_profile",
    "build_compilation_manifest",
    "build_compiler_identity",
    "compile_identity_vector_artifact",
    "compile_identity_vector_library",
    "compiled_artifact_is_current",
    "current_git_commit",
    "list_compilable_profile_keys",
    "load_compiled_identity_vector",
    "save_compilation_manifest",
    "save_compiled_identity_vector",
    "sha256_file",
    "source_acf_path_for_profile",
    "storage_reduction_ratio",
]
