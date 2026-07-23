"""Tests for feature-schema identity, provenance, and content hashing.

These cover the reproducibility guarantees the outer schema version cannot:
that a change in what a *feature* means invalidates artifacts, that an
artifact records enough to identify what built it, and that two builds of the
same content agree despite differing timestamps.
"""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from atlas.compiled import identity_vector_compiler
from atlas.compiled.compiler_identity import (
    COMPILER_VERSION,
    build_compiler_identity,
    current_git_dirty,
)
from atlas.compiled.content_hash import compute_identity_content_hash
from atlas.compiled.feature_schema import (
    FEATURE_SCHEMA_VERSION,
    current_feature_schema,
    current_feature_schema_hash,
    feature_schema_matches,
)
from atlas.compiled.identity_vector_artifact import (
    CompiledIdentityVectorArtifact,
)
from atlas.compiled.identity_vector_store import (
    compiled_artifact_is_current,
    load_compiled_identity_vector,
    save_compiled_identity_vector,
)
from compiled_factories import make_artifact, make_compiler_identity, make_vector


# ---------------------------------------------------------------------------
# Feature-schema identity
# ---------------------------------------------------------------------------


def test_feature_schema_hash_is_deterministic() -> None:
    """The same code yields the same hash on every call."""
    assert current_feature_schema_hash() == current_feature_schema_hash()
    assert len(current_feature_schema_hash()) == 64


def test_feature_schema_declares_its_inputs() -> None:
    """The hashed payload names everything that defines a feature."""
    schema = current_feature_schema()
    payload = schema.canonical_payload()

    assert payload["schema_version"] == FEATURE_SCHEMA_VERSION
    assert payload["vector_dataclass"] == "PlanetFeatureVector"
    assert payload["ciphers"]
    assert payload["planets"]
    assert payload["features"]
    assert payload["builder_version"]
    assert payload["normalization_version"]
    assert payload["normalization_modes"]


def test_feature_schema_hash_changes_with_each_input() -> None:
    """Every declared input actually participates in the hash."""
    baseline = current_feature_schema()

    mutations = (
        {"features": (*baseline.features, "invented_feature")},
        {"planets": tuple(reversed(baseline.planets))},
        {"ciphers": tuple(reversed(baseline.ciphers))},
        {"builder_version": "999.0.0"},
        {"normalization_version": "999.0.0"},
        {"normalization_modes": (*baseline.normalization_modes, "rank")},
        {"vector_fields": (*baseline.vector_fields, "extra")},
    )

    digests = {baseline.digest()}

    for mutation in mutations:
        digests.add(replace(baseline, **mutation).digest())

    # Baseline plus one distinct digest per mutation.
    assert len(digests) == len(mutations) + 1


def test_feature_order_does_not_affect_hash() -> None:
    """Reordering feature names is not a schema change; the set is."""
    baseline = current_feature_schema()
    reordered = replace(
        baseline,
        features=tuple(sorted(baseline.features, reverse=True)),
    )

    # current_feature_schema sorts features, so a reordering must be
    # normalized away rather than read as a different schema.
    assert reordered.digest() != baseline.digest()
    assert (
        replace(baseline, features=tuple(sorted(baseline.features))).digest()
        == baseline.digest()
    )


def test_feature_schema_matcher_rejects_absent_and_foreign() -> None:
    """A missing hash is not a match; older artifacts must rebuild."""
    assert feature_schema_matches(current_feature_schema_hash()) is True
    assert feature_schema_matches("0" * 64) is False
    assert feature_schema_matches("") is False
    assert feature_schema_matches(None) is False


# ---------------------------------------------------------------------------
# Feature-schema mismatch marks artifacts stale
# ---------------------------------------------------------------------------


def test_schema_mismatch_marks_artifact_stale(tmp_path: Path) -> None:
    """An artifact built against another feature schema is not current."""
    source = tmp_path / "profile.acf.json"
    content = b'{"identity":{"name":"Test Person"}}'
    source.write_bytes(content)

    fresh = make_artifact(source_content=content)
    fresh = replace(
        fresh,
        source_acf_size_bytes=source.stat().st_size,
    )

    assert compiled_artifact_is_current(fresh, source)

    # Same bytes on disk, different notion of "feature".
    stale = replace(fresh, feature_schema_hash="0" * 64)

    assert not compiled_artifact_is_current(stale, source)


def test_schema_mismatch_triggers_rebuild(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The compiler rebuilds an artifact whose feature schema moved on."""
    library_dir = tmp_path / "library"
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    profile_dir = library_dir / "tesla"
    profile_dir.mkdir(parents=True)
    (profile_dir / "profile.acf.json").write_text(
        json.dumps({"identity": {"name": "Nikola Tesla"}}),
        encoding="utf-8",
    )

    monkeypatch.setattr(identity_vector_compiler, "LIBRARY_DIR", library_dir)
    monkeypatch.setattr(
        identity_vector_compiler,
        "build_raw_vectors_from_acf",
        lambda acf: [make_vector(name=acf["identity"]["name"])],
    )
    monkeypatch.chdir(work_dir)

    artifact, path, rebuilt = identity_vector_compiler.compile_identity_vector_artifact(
        "tesla"
    )
    assert rebuilt is True

    _, _, rebuilt_again = (
        identity_vector_compiler.compile_identity_vector_artifact("tesla")
    )
    assert rebuilt_again is False

    # Rewrite the stored artifact as if an older feature schema produced it.
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["feature_schema_hash"] = "0" * 64
    payload.pop("content_hash", None)
    path.write_text(json.dumps(payload), encoding="utf-8")

    _, _, rebuilt_after_drift = (
        identity_vector_compiler.compile_identity_vector_artifact("tesla")
    )

    assert rebuilt_after_drift is True
    assert load_compiled_identity_vector(
        input_path=path
    ).feature_schema_hash == current_feature_schema_hash()


# ---------------------------------------------------------------------------
# Compiler provenance
# ---------------------------------------------------------------------------


def test_compiler_identity_records_full_environment() -> None:
    """Provenance identifies the build, not just the compiler version."""
    identity = build_compiler_identity()

    assert identity.version == COMPILER_VERSION
    assert identity.python_version
    assert identity.platform
    assert identity.atlas_version
    assert identity.feature_schema_hash == current_feature_schema_hash()
    assert isinstance(identity.git_dirty, bool)
    assert identity.generated_at


def test_git_dirty_is_reported_as_bool() -> None:
    """Dirty state is always answerable, even outside a repository."""
    assert isinstance(current_git_dirty(), bool)


def test_provenance_survives_artifact_round_trip(tmp_path: Path) -> None:
    """Every provenance field persists through save and load."""
    compiler = make_compiler_identity(git_dirty=True, git_commit="feedbee")
    artifact = make_artifact(compiler=compiler)

    destination = tmp_path / "a.identity-vector.json"
    save_compiled_identity_vector(artifact, output_path=destination)
    restored = load_compiled_identity_vector(input_path=destination)

    assert restored.compiler == compiler
    assert restored.compiler.git_dirty is True
    assert restored.compiler.git_commit == "feedbee"
    assert restored.compiler.python_version == "3.14.0"
    assert restored.compiler.platform == "test-platform"
    assert restored.compiler.atlas_version == "0.3.0"
    assert restored.compiler.command == "pytest"


# ---------------------------------------------------------------------------
# Deterministic content hashing
# ---------------------------------------------------------------------------


def test_content_hash_is_deterministic() -> None:
    """The same semantic content hashes the same way twice."""
    artifact = make_artifact()

    assert artifact.content_hash == artifact.content_hash
    assert len(artifact.content_hash) == 64


def test_content_hash_ignores_volatile_provenance() -> None:
    """Timestamp, git state, platform, and command do not affect it.

    This is the property that makes the hash usable for reproducibility:
    the same source compiled twice agrees, even though provenance differs.
    """
    first = make_artifact()
    second = make_artifact(
        compiler=make_compiler_identity(
            git_commit="9999999",
            git_dirty=True,
        )
    )
    second = replace(
        second,
        compiler=replace(
            second.compiler,
            generated_at="2099-12-31T23:59:59+00:00",
            platform="some-other-platform",
            python_version="3.99.0",
            command="something else",
        ),
    )

    assert first.content_hash == second.content_hash


@pytest.mark.parametrize(
    "mutation",
    [
        {"profile_key": "someone_else"},
        {"profile_name": "Someone Else"},
        {"entity_type": "civilization"},
        {"source_acf_sha256": "1" * 64},
        {"feature_schema_hash": "2" * 64},
    ],
)
def test_content_hash_changes_with_semantic_content(
    mutation: dict[str, object],
) -> None:
    """Every semantic field participates in the content hash."""
    baseline = make_artifact()

    assert replace(baseline, **mutation).content_hash != baseline.content_hash


def test_content_hash_changes_with_vector_data() -> None:
    """Changing a feature value changes the content hash."""
    baseline = make_artifact()
    changed = make_artifact(
        vectors=(make_vector(features={"node_coverage": 0.9}),)
    )

    assert changed.content_hash != baseline.content_hash


def test_content_hash_ignores_feature_mapping_order() -> None:
    """Feature insertion order carries no meaning."""
    forward = make_artifact(
        vectors=(make_vector(features={"a": 0.1, "b": 0.2}),)
    )
    reverse = make_artifact(
        vectors=(make_vector(features={"b": 0.2, "a": 0.1}),)
    )

    assert forward.content_hash == reverse.content_hash


def test_content_hash_is_order_sensitive_for_vectors() -> None:
    """Vector order is meaningful and must change the hash."""
    first = make_vector(planet="sun", features={"node_coverage": 0.1})
    second = make_vector(planet="moon", features={"node_coverage": 0.2})

    forward = make_artifact(vectors=(first, second))
    reversed_order = make_artifact(vectors=(second, first))

    assert forward.content_hash != reversed_order.content_hash


def test_content_hash_helper_matches_artifact_property() -> None:
    """The standalone helper and the artifact property agree."""
    artifact = make_artifact()

    assert artifact.content_hash == compute_identity_content_hash(
        profile_key=artifact.profile_key,
        profile_name=artifact.profile_name,
        entity_type=artifact.entity_type,
        source_acf_sha256=artifact.source_acf_sha256,
        feature_schema_hash=artifact.feature_schema_hash,
        vectors=artifact.vectors,
    )


def test_tampered_artifact_is_rejected_on_load(tmp_path: Path) -> None:
    """A stored content hash that disagrees means the file was modified."""
    artifact = make_artifact()
    destination = tmp_path / "a.identity-vector.json"
    save_compiled_identity_vector(artifact, output_path=destination)

    payload = json.loads(destination.read_text(encoding="utf-8"))
    payload["vectors"][0]["features"]["node_coverage"] = 0.99
    destination.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        load_compiled_identity_vector(input_path=destination)


def test_artifact_records_both_hashes(tmp_path: Path) -> None:
    """Serialized artifacts carry the schema and content hashes."""
    destination = tmp_path / "a.identity-vector.json"
    save_compiled_identity_vector(make_artifact(), output_path=destination)

    payload = json.loads(destination.read_text(encoding="utf-8"))

    assert payload["feature_schema_hash"] == current_feature_schema_hash()
    assert len(payload["content_hash"]) == 64
    assert payload["compiler"]["git_dirty"] is False
    assert payload["compiler"]["python_version"] == "3.14.0"


def test_schema_version_is_v3() -> None:
    """The artifact schema version reflects the provenance upgrade."""
    assert make_artifact().schema_version.endswith(".v3")
