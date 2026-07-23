"""Persistent storage for compiled identity-vector artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from atlas.compiled.hashing import sha256_file
from atlas.compiled.identity_vector_artifact import (
    CompiledIdentityVectorArtifact,
)


DEFAULT_COMPILED_VECTOR_DIR = (
    Path("output")
    / "compiled"
    / "identity_vectors"
)


def artifact_path_for_profile(
    profile_key: str,
    *,
    output_dir: Path = DEFAULT_COMPILED_VECTOR_DIR,
) -> Path:
    """Return the canonical compiled artifact path for a profile."""
    safe_key = profile_key.strip()

    if not safe_key:
        raise ValueError("Profile key cannot be empty.")

    if safe_key in {".", ".."}:
        raise ValueError("Invalid profile key.")

    return output_dir / f"{safe_key}.identity-vector.json"


def save_compiled_identity_vector(
    artifact: CompiledIdentityVectorArtifact,
    *,
    output_path: Path | None = None,
) -> Path:
    """Write a compiled artifact atomically."""
    destination = output_path or artifact_path_for_profile(
        artifact.profile_key
    )
    destination.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = destination.with_suffix(
        destination.suffix + ".tmp"
    )

    temporary_path.write_text(
        json.dumps(
            artifact.to_dict(),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(destination)

    return destination


def load_compiled_identity_vector(
    profile_key: str | None = None,
    *,
    input_path: Path | None = None,
) -> CompiledIdentityVectorArtifact:
    """Load and validate one compiled identity-vector artifact."""
    if input_path is None:
        if profile_key is None:
            raise ValueError(
                "Either profile_key or input_path must be supplied."
            )

        input_path = artifact_path_for_profile(profile_key)

    payload = json.loads(input_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Compiled artifact root must be an object.")

    return CompiledIdentityVectorArtifact.from_dict(payload)


def compiled_artifact_is_current(
    artifact: CompiledIdentityVectorArtifact,
    source_acf_path: Path,
) -> bool:
    """Return whether an artifact matches the current ACF content."""
    if not source_acf_path.is_file():
        return False

    stat = source_acf_path.stat()

    if artifact.source_acf_size_bytes != stat.st_size:
        return False

    return artifact.source_acf_sha256 == sha256_file(source_acf_path)
