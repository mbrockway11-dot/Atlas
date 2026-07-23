"""Tests for the compiled corpus index."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.compiled.identity_vector_store import save_compiled_identity_vector
from atlas.compiled.index import (
    COMPILED_INDEX_SCHEMA,
    CompiledIndex,
    build_compiled_index,
    load_compiled_index,
    save_compiled_index,
)
from atlas.ive.schema import PlanetFeatureVector
from compiled_factories import make_artifact, make_vector


def _write_artifact(
    artifact_dir: Path,
    profile_key: str,
    *,
    profile_name: str,
    entity_type: str = "person",
    vector_count: int = 2,
) -> Path:
    """Persist a compiled artifact into an artifact directory."""
    vectors = tuple(
        make_vector(name=profile_key, planet=f"planet_{index}")
        for index in range(vector_count)
    )

    artifact = make_artifact(
        profile_key,
        vectors,
        profile_name=profile_name,
        entity_type=entity_type,
        source_acf_sha256=(profile_key * 64)[:64],
        source_acf_size_bytes=2_048,
        source_acf_path=f"library/{profile_key}/profile.acf.json",
    )

    return save_compiled_identity_vector(
        artifact,
        output_path=artifact_dir / f"{profile_key}.identity-vector.json",
    )


@pytest.fixture
def artifact_dir(tmp_path: Path) -> Path:
    """Build a small compiled corpus on disk."""
    directory = tmp_path / "compiled" / "identity_vectors"
    directory.mkdir(parents=True)

    _write_artifact(directory, "nikola_tesla", profile_name="Nikola Tesla")
    _write_artifact(
        directory,
        "roman_empire",
        profile_name="Roman Empire",
        entity_type="civilization",
        vector_count=3,
    )

    return directory


def test_index_records_profile_metadata(artifact_dir: Path) -> None:
    """Each entry carries the metadata needed to route a request."""
    index = build_compiled_index(artifact_dir=artifact_dir)

    assert index.schema_version == COMPILED_INDEX_SCHEMA
    assert index.profile_count == 2
    assert index.total_vector_count == 5
    assert index.total_artifact_bytes > 0

    entry = index.entries["nikola_tesla"]

    assert entry.profile_name == "Nikola Tesla"
    assert entry.entity_type == "person"
    assert entry.vector_count == 2
    assert len(entry.source_hash) == 64
    assert entry.artifact_bytes > 0


def test_index_paths_are_relative_and_portable(artifact_dir: Path) -> None:
    """Recorded paths are relative, so the index survives a move."""
    index = build_compiled_index(artifact_dir=artifact_dir)
    entry = index.entries["nikola_tesla"]

    assert entry.path == (
        "identity_vectors/nikola_tesla.identity-vector.json"
    )
    assert not Path(entry.path).is_absolute()


def test_index_supports_entity_type_filtering(artifact_dir: Path) -> None:
    """Entity type is queryable without opening any artifact."""
    index = build_compiled_index(artifact_dir=artifact_dir)

    assert index.keys_by_entity_type("person") == ("nikola_tesla",)
    assert index.keys_by_entity_type("civilization") == ("roman_empire",)
    assert index.entity_type_counts() == {
        "civilization": 1,
        "person": 1,
    }


def test_index_flags_irregular_vector_counts(artifact_dir: Path) -> None:
    """Off-nominal vector counts are surfaced, not assumed away."""
    index = build_compiled_index(artifact_dir=artifact_dir)

    assert index.irregular_keys(2) == ("roman_empire",)
    assert index.irregular_keys(3) == ("nikola_tesla",)


def test_index_ties_to_the_corpus_revision(artifact_dir: Path) -> None:
    """The index hash tracks the exact set of source revisions."""
    baseline = build_compiled_index(artifact_dir=artifact_dir)

    _write_artifact(artifact_dir, "ada_lovelace", profile_name="Ada Lovelace")

    extended = build_compiled_index(artifact_dir=artifact_dir)

    assert len(baseline.source_manifest_hash) == 64
    assert extended.source_manifest_hash != baseline.source_manifest_hash
    assert extended.profile_count == 3


def test_index_skips_damaged_artifacts(artifact_dir: Path) -> None:
    """One unreadable artifact never aborts the scan."""
    (artifact_dir / "broken.identity-vector.json").write_text(
        "{not json",
        encoding="utf-8",
    )

    index = build_compiled_index(artifact_dir=artifact_dir)

    assert "broken" not in index.entries
    assert index.profile_count == 2


def test_index_round_trip(artifact_dir: Path, tmp_path: Path) -> None:
    """The index survives a save/load cycle exactly."""
    index = build_compiled_index(artifact_dir=artifact_dir)
    path = save_compiled_index(index, output_path=tmp_path / "index.json")
    restored = load_compiled_index(input_path=path)

    assert restored.entries == index.entries
    assert restored.source_manifest_hash == index.source_manifest_hash
    assert restored.total_vector_count == index.total_vector_count
    assert path.read_text(encoding="utf-8").endswith("\n")


def test_index_rejects_unsupported_schema(artifact_dir: Path) -> None:
    """A foreign index schema is rejected rather than guessed at."""
    payload = build_compiled_index(artifact_dir=artifact_dir).to_dict()
    payload["schema_version"] = "atlas.compiled.index.v99"

    with pytest.raises(ValueError, match="Unsupported compiled index"):
        CompiledIndex.from_dict(payload)


def test_index_rejects_non_object_root(tmp_path: Path) -> None:
    """A JSON array is not a valid index document."""
    path = tmp_path / "index.json"
    path.write_text(json.dumps([1, 2]), encoding="utf-8")

    with pytest.raises(ValueError, match="must be an object"):
        load_compiled_index(input_path=path)


def test_index_requires_an_artifact_directory(tmp_path: Path) -> None:
    """A missing artifact directory is an explicit failure."""
    with pytest.raises(FileNotFoundError):
        build_compiled_index(artifact_dir=tmp_path / "absent")
