"""Compiler from Atlas ACF profiles into compact vector artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from atlas.compiled.compiler_identity import build_compiler_identity
from atlas.compiled.hashing import sha256_file
from atlas.compiled.identity_vector_artifact import (
    COMPILED_IDENTITY_VECTOR_SCHEMA,
    CompiledIdentityVectorArtifact,
)
from atlas.compiled.identity_vector_store import (
    artifact_path_for_profile,
    compiled_artifact_is_current,
    load_compiled_identity_vector,
    save_compiled_identity_vector,
)
from atlas.ive import build_raw_vectors_from_acf
from atlas.library.profile_library import LIBRARY_DIR


def source_acf_path_for_profile(profile_key: str) -> Path:
    """Return the canonical ACF source path for a saved profile."""
    return LIBRARY_DIR / profile_key / "profile.acf.json"


def compile_identity_vector_artifact(
    profile_key: str,
    *,
    force: bool = False,
) -> tuple[CompiledIdentityVectorArtifact, Path, bool]:
    """Compile one saved ACF into a reusable vector artifact."""
    clean_profile_key = profile_key.strip()

    if not clean_profile_key:
        raise ValueError("Profile key cannot be empty.")

    source_path = source_acf_path_for_profile(clean_profile_key)
    output_path = artifact_path_for_profile(clean_profile_key)

    if not source_path.is_file():
        raise FileNotFoundError(
            f"ACF profile does not exist: {source_path}"
        )

    if not force:
        try:
            current = load_compiled_identity_vector(
                clean_profile_key
            )

            if compiled_artifact_is_current(current, source_path):
                return current, output_path, False
        except (
            FileNotFoundError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ):
            pass

    source_bytes = source_path.read_bytes()
    acf = json.loads(source_bytes.decode("utf-8-sig"))

    if not isinstance(acf, dict):
        raise ValueError(
            f"ACF root must be an object: {source_path}"
        )

    identity = acf.get("identity")

    if not isinstance(identity, dict):
        raise ValueError(
            f"ACF profile has no valid identity block: {source_path}"
        )

    profile_name = identity.get("name")

    if not profile_name:
        raise ValueError(
            f"ACF identity has no profile name: {source_path}"
        )

    raw_vectors = tuple(build_raw_vectors_from_acf(acf))

    if not raw_vectors:
        raise ValueError(
            f"ACF produced no raw identity vectors: {clean_profile_key}"
        )

    compiler = build_compiler_identity()

    artifact = CompiledIdentityVectorArtifact(
        schema_version=COMPILED_IDENTITY_VECTOR_SCHEMA,
        profile_key=clean_profile_key,
        profile_name=str(profile_name),
        entity_type=str(identity.get("entity_type", "person")),
        compiler_name=compiler.name,
        compiler_version=compiler.version,
        compiler_git_commit=compiler.git_commit,
        compiled_at=compiler.generated_at,
        source_acf_path=str(source_path),
        source_acf_sha256=sha256_file(source_path),
        source_acf_size_bytes=len(source_bytes),
        vector_count=len(raw_vectors),
        vectors=raw_vectors,
    )

    saved_path = save_compiled_identity_vector(
        artifact,
        output_path=output_path,
    )

    return artifact, saved_path, True
