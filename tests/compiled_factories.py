"""Shared constructors for compiled-artifact tests.

Building a ``CompiledIdentityVectorArtifact`` by hand means filling in a full
provenance block that most tests do not care about. These factories supply
fixed, deterministic defaults so a test states only what it is actually
testing -- and so a future artifact-schema change updates one file rather
than every test module that happens to build an artifact.

Defaults are deliberately fixed strings, never ``datetime.now()`` or the real
git state, so artifacts built here are byte-stable across runs.
"""

from __future__ import annotations

import hashlib

from atlas.compiled.compiler_identity import CompilerIdentity
from atlas.compiled.feature_schema import current_feature_schema_hash
from atlas.compiled.identity_vector_artifact import (
    COMPILED_IDENTITY_VECTOR_SCHEMA,
    CompiledIdentityVectorArtifact,
)
from atlas.ive.schema import VECTOR_FEATURES, PlanetFeatureVector


FIXED_COMPILED_AT = "2026-01-01T00:00:00+00:00"


def make_compiler_identity(
    *,
    version: str = "1.2.0",
    git_commit: str = "abc1234",
    git_dirty: bool = False,
    feature_schema_hash: str | None = None,
) -> CompilerIdentity:
    """Return a deterministic compiler-provenance block.

    ``feature_schema_hash`` defaults to the *current* schema so artifacts
    built here read as fresh; pass an explicit value to simulate an artifact
    compiled against a different feature schema.
    """
    return CompilerIdentity(
        name="Atlas Identity Vector Compiler",
        version=version,
        git_commit=git_commit,
        git_dirty=git_dirty,
        python_version="3.14.0",
        platform="test-platform",
        atlas_version="0.3.0",
        feature_schema_hash=(
            current_feature_schema_hash()
            if feature_schema_hash is None
            else feature_schema_hash
        ),
        command="pytest",
        generated_at=FIXED_COMPILED_AT,
    )


def make_vector(
    *,
    name: str = "Test Person",
    cipher: str = "ordinal",
    planet: str = "sun",
    features: dict[str, float] | None = None,
    full_schema: bool = False,
) -> PlanetFeatureVector:
    """Return one raw planet-feature vector.

    ``full_schema`` fills every declared feature, for tests that exercise
    normalization; otherwise a small explicit feature set keeps assertions
    readable.
    """
    if features is None:
        features = (
            {feature: 0.5 for feature in VECTOR_FEATURES}
            if full_schema
            else {"node_coverage": 0.5, "loop_ratio": 0.25}
        )

    return PlanetFeatureVector(
        version="test",
        name=name,
        cipher=cipher,
        planet=planet,
        kamea=planet,
        grid_size=6,
        features=dict(features),
    )


def make_artifact(
    profile_key: str = "test_person",
    vectors: tuple[PlanetFeatureVector, ...] | None = None,
    *,
    profile_name: str | None = None,
    entity_type: str = "person",
    source_content: bytes = b'{"identity":{"name":"Test Person"}}',
    source_acf_sha256: str | None = None,
    source_acf_size_bytes: int | None = None,
    source_acf_path: str = "profile.acf.json",
    compiler: CompilerIdentity | None = None,
    feature_schema_hash: str | None = None,
    vector_count: int | None = None,
) -> CompiledIdentityVectorArtifact:
    """Return a compiled artifact with deterministic provenance."""
    resolved_vectors = (
        (make_vector(),) if vectors is None else tuple(vectors)
    )
    resolved_compiler = compiler or make_compiler_identity()

    return CompiledIdentityVectorArtifact(
        schema_version=COMPILED_IDENTITY_VECTOR_SCHEMA,
        profile_key=profile_key,
        profile_name=(
            profile_name
            if profile_name is not None
            else profile_key.replace("_", " ").title()
        ),
        entity_type=entity_type,
        feature_schema_hash=(
            resolved_compiler.feature_schema_hash
            if feature_schema_hash is None
            else feature_schema_hash
        ),
        compiler=resolved_compiler,
        source_acf_path=source_acf_path,
        source_acf_sha256=(
            hashlib.sha256(source_content).hexdigest()
            if source_acf_sha256 is None
            else source_acf_sha256
        ),
        source_acf_size_bytes=(
            len(source_content)
            if source_acf_size_bytes is None
            else source_acf_size_bytes
        ),
        vector_count=(
            len(resolved_vectors) if vector_count is None else vector_count
        ),
        vectors=resolved_vectors,
    )
