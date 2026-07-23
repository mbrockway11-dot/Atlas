"""Tests for compiled identity-vector artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from atlas.compiled.hashing import sha256_file
from atlas.compiled.identity_vector_artifact import (
    CompiledIdentityVectorArtifact,
)
from atlas.compiled.identity_vector_store import (
    compiled_artifact_is_current,
    load_compiled_identity_vector,
    save_compiled_identity_vector,
)
from atlas.compiled.manifest import (
    COMPILED_MANIFEST_SCHEMA,
    build_compilation_manifest,
)
from atlas.ive import PlanetFeatureVector
from compiled_factories import make_artifact, make_vector


@pytest.fixture
def sample_vector() -> PlanetFeatureVector:
    """Return one representative raw vector."""
    return make_vector()


@pytest.fixture
def sample_artifact(
    sample_vector: PlanetFeatureVector,
) -> CompiledIdentityVectorArtifact:
    """Return a representative compiled artifact."""
    return make_artifact(vectors=(sample_vector,))


def test_artifact_round_trip_preserves_vectors(
    sample_artifact: CompiledIdentityVectorArtifact,
) -> None:
    """Serialization must preserve all vector information."""
    restored = CompiledIdentityVectorArtifact.from_dict(
        sample_artifact.to_dict()
    )

    assert restored == sample_artifact
    assert restored.vectors[0].features["node_coverage"] == 0.5


def test_store_round_trip(
    tmp_path: Path,
    sample_artifact: CompiledIdentityVectorArtifact,
) -> None:
    """The JSON store must persist and restore an artifact."""
    destination = tmp_path / "test.identity-vector.json"

    save_compiled_identity_vector(
        sample_artifact,
        output_path=destination,
    )

    restored = load_compiled_identity_vector(
        input_path=destination,
    )

    assert restored == sample_artifact
    assert json.loads(destination.read_text())["vector_count"] == 1


def test_vector_count_mismatch_is_rejected(
    sample_artifact: CompiledIdentityVectorArtifact,
) -> None:
    """Damaged vector counts must be rejected."""
    payload = sample_artifact.to_dict()
    payload["vector_count"] = 2

    with pytest.raises(ValueError, match="vector count mismatch"):
        CompiledIdentityVectorArtifact.from_dict(payload)


def test_unknown_schema_is_rejected(
    sample_artifact: CompiledIdentityVectorArtifact,
) -> None:
    """Incompatible schemas must be rejected."""
    payload = sample_artifact.to_dict()
    payload["schema_version"] = "unknown-schema"

    with pytest.raises(ValueError, match="Unsupported"):
        CompiledIdentityVectorArtifact.from_dict(payload)


def test_sha256_file_matches_hashlib(tmp_path: Path) -> None:
    """File hashing must match the standard library digest."""
    source = tmp_path / "source.json"
    content = b'{"test":true}'
    source.write_bytes(content)

    assert sha256_file(source) == hashlib.sha256(content).hexdigest()


def test_current_artifact_uses_content_hash(
    tmp_path: Path,
    sample_artifact: CompiledIdentityVectorArtifact,
) -> None:
    """Freshness must be based on source content."""
    source = tmp_path / "profile.acf.json"
    source.write_bytes(b'{"identity":{"name":"Test Person"}}')

    current = replace(
        sample_artifact,
        source_acf_sha256=sha256_file(source),
        source_acf_size_bytes=source.stat().st_size,
    )

    assert compiled_artifact_is_current(current, source)

    source.write_bytes(b'{"identity":{"name":"Changed"}}')

    assert not compiled_artifact_is_current(current, source)


def test_manifest_records_compilation_counts() -> None:
    """Manifest construction must preserve compilation statistics."""
    manifest = build_compilation_manifest(
        requested_count=10,
        successful_count=9,
        rebuilt_count=7,
        reused_count=2,
        failed_count=1,
        total_vector_count=189,
        total_source_bytes=1000,
        total_artifact_bytes=100,
        failures=(
            {
                "profile_key": "broken",
                "error": "missing ACF",
            },
        ),
    )

    assert manifest.schema_version == COMPILED_MANIFEST_SCHEMA
    assert manifest.successful_count == 9
    assert manifest.failed_count == 1
    assert manifest.total_vector_count == 189
