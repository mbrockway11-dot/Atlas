"""Tests for the batch identity-vector library compiler."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from atlas.compiled import identity_vector_compiler
from atlas.compiled.identity_vector_artifact import (
    COMPILED_IDENTITY_VECTOR_SCHEMA,
    CompiledIdentityVectorArtifact,
)
from atlas.compiled.identity_vector_library_compiler import (
    EXPECTED_VECTOR_COUNT,
    compile_identity_vector_library,
    list_compilable_profile_keys,
    storage_reduction_ratio,
)
from atlas.compiled.identity_vector_store import artifact_path_for_profile
from atlas.compiled.manifest import COMPILED_MANIFEST_SCHEMA
from atlas.ive import PlanetFeatureVector
from compiled_factories import make_artifact, make_vector


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_acf(library_dir: Path, profile_key: str, name: str) -> Path:
    """Create a minimal saved ACF profile inside a library directory."""
    profile_dir = library_dir / profile_key
    profile_dir.mkdir(parents=True, exist_ok=True)

    acf_path = profile_dir / "profile.acf.json"
    acf_path.write_text(
        json.dumps({"identity": {"name": name}}),
        encoding="utf-8",
    )

    return acf_path


def _artifact_for(
    profile_key: str,
    *,
    vector_count: int = EXPECTED_VECTOR_COUNT,
    source_bytes: int = 2_134_000,
) -> CompiledIdentityVectorArtifact:
    """Build a representative compiled artifact for a fake compile result."""
    vector = make_vector(
        name=profile_key,
        features={"node_coverage": 0.5},
    )

    return make_artifact(
        profile_key,
        tuple(vector for _ in range(vector_count)),
        profile_name=profile_key,
        source_acf_path=f"{profile_key}/profile.acf.json",
        source_acf_sha256=hashlib.sha256(profile_key.encode()).hexdigest(),
        source_acf_size_bytes=source_bytes,
        vector_count=vector_count,
    )


def _make_fake_compile(artifact_dir: Path, *, artifact_size: int = 19_000):
    """Return a fake compile_func writing a small artifact file per key."""
    artifact_dir.mkdir(parents=True, exist_ok=True)

    def fake_compile(profile_key: str, *, force: bool = False):
        artifact = _artifact_for(profile_key)
        output_path = artifact_dir / f"{profile_key}.identity-vector.json"
        output_path.write_text("x" * artifact_size, encoding="utf-8")
        rebuilt = not profile_key.endswith("_reused")
        return artifact, output_path, rebuilt

    return fake_compile


def _fake_raw_vectors(acf: dict) -> tuple[PlanetFeatureVector, ...]:
    """Deterministic 21-vector stand-in keyed on the profile name."""
    name = acf["identity"]["name"]
    return tuple(
        PlanetFeatureVector(
            version="stub",
            name=name,
            cipher="ordinal",
            planet="sun",
            kamea="sun",
            grid_size=6,
            features={"node_coverage": 0.5},
        )
        for _ in range(EXPECTED_VECTOR_COUNT)
    )


# ---------------------------------------------------------------------------
# Enumeration + key selection
# ---------------------------------------------------------------------------


def test_lists_only_profiles_with_acf(tmp_path: Path) -> None:
    """Only directories with an ACF source are compilable."""
    _write_acf(tmp_path, "nikola_tesla", "Nikola Tesla")
    _write_acf(tmp_path, "ada_lovelace", "Ada Lovelace")
    (tmp_path / "no_acf").mkdir()

    assert list_compilable_profile_keys(library_dir=tmp_path) == (
        "ada_lovelace",
        "nikola_tesla",
    )


def test_uses_key_source_by_default(tmp_path: Path) -> None:
    """With no keys or library_dir, the key_source registry is used."""
    result = compile_identity_vector_library(
        key_source=lambda: ["tesla", "curie"],
        write_manifest=False,
        compile_func=_make_fake_compile(tmp_path / "a"),
    )

    assert result.manifest.requested_count == 2
    assert {o.profile_key for o in result.outcomes} == {"tesla", "curie"}


def test_limit_caps_processed_profiles(tmp_path: Path) -> None:
    """--limit restricts how many profiles are compiled."""
    result = compile_identity_vector_library(
        profile_keys=["a", "b", "c", "d", "e"],
        limit=2,
        write_manifest=False,
        compile_func=_make_fake_compile(tmp_path / "a"),
    )

    assert result.manifest.requested_count == 2
    assert len(result.outcomes) == 2


def test_negative_limit_is_rejected(tmp_path: Path) -> None:
    """A negative limit is a programming error."""
    with pytest.raises(ValueError, match="limit cannot be negative"):
        compile_identity_vector_library(
            profile_keys=["a"],
            limit=-1,
            write_manifest=False,
            compile_func=_make_fake_compile(tmp_path / "a"),
        )


def test_requested_keys_are_cleaned_and_deduped(tmp_path: Path) -> None:
    """Whitespace is trimmed, blanks dropped, duplicates collapsed."""
    calls: list[str] = []

    def fake_compile(profile_key: str, *, force: bool = False):
        calls.append(profile_key)
        output_path = tmp_path / f"{profile_key}.json"
        output_path.write_text("x", encoding="utf-8")
        return _artifact_for(profile_key), output_path, True

    result = compile_identity_vector_library(
        profile_keys=["  tesla  ", "tesla", "", "   ", "curie"],
        write_manifest=False,
        compile_func=fake_compile,
    )

    assert calls == ["tesla", "curie"]
    assert result.manifest.requested_count == 2


# ---------------------------------------------------------------------------
# Counts, invariants, totals, reduction
# ---------------------------------------------------------------------------


def test_successful_compilation_counts_and_invariants(
    tmp_path: Path,
) -> None:
    """Success path: counts, totals, reduction, and invariants hold."""
    result = compile_identity_vector_library(
        profile_keys=["a", "b", "c"],
        write_manifest=False,
        compile_func=_make_fake_compile(tmp_path / "art", artifact_size=19_000),
    )

    m = result.manifest

    assert m.requested_count == 3
    assert m.successful_count == 3
    assert m.rebuilt_count == 3
    assert m.reused_count == 0
    assert m.failed_count == 0
    assert m.total_vector_count == 3 * EXPECTED_VECTOR_COUNT
    assert m.total_source_bytes == 3 * 2_134_000
    assert m.total_artifact_bytes == 3 * 19_000

    # Documented invariants.
    assert m.successful_count == m.rebuilt_count + m.reused_count
    assert m.requested_count == m.successful_count + m.failed_count

    # Derived statistics.
    assert m.average_source_bytes == pytest.approx(2_134_000)
    assert m.average_artifact_bytes == pytest.approx(19_000)
    assert m.storage_reduction_percent == pytest.approx(
        (1 - 19_000 / 2_134_000) * 100
    )
    assert m.storage_reduction_percent > 99.0
    assert storage_reduction_ratio(m) > 0.99
    assert m.elapsed_seconds >= 0.0


def test_reuse_and_rebuild_counts(tmp_path: Path) -> None:
    """rebuilt/reused counts follow the per-profile rebuilt flag."""
    result = compile_identity_vector_library(
        profile_keys=["a_rebuilt", "b_reused", "c_rebuilt"],
        write_manifest=False,
        compile_func=_make_fake_compile(tmp_path / "art"),
    )

    m = result.manifest
    assert m.rebuilt_count == 2
    assert m.reused_count == 1
    assert m.successful_count == m.rebuilt_count + m.reused_count


# ---------------------------------------------------------------------------
# Failures
# ---------------------------------------------------------------------------


def test_one_broken_profile_does_not_stop_batch(tmp_path: Path) -> None:
    """A single failure is recorded; remaining profiles still compile."""
    artifact_dir = tmp_path / "art"
    artifact_dir.mkdir()

    def fake_compile(profile_key: str, *, force: bool = False):
        if profile_key == "broken":
            raise FileNotFoundError("ACF profile does not exist")
        output_path = artifact_dir / f"{profile_key}.json"
        output_path.write_text("payload", encoding="utf-8")
        return _artifact_for(profile_key), output_path, True

    result = compile_identity_vector_library(
        profile_keys=["good_one", "broken", "good_two"],
        write_manifest=False,
        compile_func=fake_compile,
    )

    m = result.manifest
    assert m.requested_count == 3
    assert m.successful_count == 2
    assert m.failed_count == 1
    assert m.requested_count == m.successful_count + m.failed_count


def test_failure_is_serialized_with_type_and_message(tmp_path: Path) -> None:
    """Failures retain profile key, error type, and message."""

    def fake_compile(profile_key: str, *, force: bool = False):
        raise ValueError("no valid identity block")

    result = compile_identity_vector_library(
        profile_keys=["broken"],
        write_manifest=False,
        compile_func=fake_compile,
    )

    assert result.manifest.failures == (
        {
            "profile_key": "broken",
            "error_type": "ValueError",
            "error": "no valid identity block",
        },
    )

    broken = result.outcomes[0]
    assert broken.success is False
    assert broken.output_path is None
    assert broken.vector_count == 0


def test_fail_fast_stops_after_first_failure(tmp_path: Path) -> None:
    """--fail-fast stops the batch at the first failing profile."""
    calls: list[str] = []
    artifact_dir = tmp_path / "art"
    artifact_dir.mkdir()

    def fake_compile(profile_key: str, *, force: bool = False):
        calls.append(profile_key)
        if profile_key == "broken":
            raise RuntimeError("boom")
        output_path = artifact_dir / f"{profile_key}.json"
        output_path.write_text("x", encoding="utf-8")
        return _artifact_for(profile_key), output_path, True

    result = compile_identity_vector_library(
        profile_keys=["ok", "broken", "never_reached"],
        fail_fast=True,
        write_manifest=False,
        compile_func=fake_compile,
    )

    assert calls == ["ok", "broken"]
    assert result.manifest.failed_count == 1
    assert result.manifest.successful_count == 1
    assert "never_reached" not in {o.profile_key for o in result.outcomes}


# ---------------------------------------------------------------------------
# Irregular vector counts
# ---------------------------------------------------------------------------


def test_irregular_vector_counts_are_reported_not_failed(
    tmp_path: Path,
) -> None:
    """Off-nominal vector counts are surfaced, not treated as failures."""
    artifact_dir = tmp_path / "art"
    artifact_dir.mkdir()

    def fake_compile(profile_key: str, *, force: bool = False):
        count = 21 if profile_key == "normal" else 14
        artifact = _artifact_for(profile_key, vector_count=count)
        output_path = artifact_dir / f"{profile_key}.json"
        output_path.write_text("x", encoding="utf-8")
        return artifact, output_path, True

    result = compile_identity_vector_library(
        profile_keys=["normal", "irregular_one"],
        write_manifest=False,
        compile_func=fake_compile,
    )

    assert result.manifest.successful_count == 2
    assert result.manifest.failed_count == 0

    irregular = result.irregular_outcomes()
    assert [o.profile_key for o in irregular] == ["irregular_one"]
    assert irregular[0].vector_count == 14


# ---------------------------------------------------------------------------
# Empty corpus + manifest writing
# ---------------------------------------------------------------------------


def test_empty_corpus_produces_empty_manifest(tmp_path: Path) -> None:
    """An empty library compiles cleanly with zero counts."""
    result = compile_identity_vector_library(
        library_dir=tmp_path / "empty",
        write_manifest=False,
    )

    m = result.manifest
    assert m.requested_count == 0
    assert m.successful_count == 0
    assert m.failed_count == 0
    assert result.outcomes == ()
    assert storage_reduction_ratio(m) == 0.0


def test_manifest_is_written_to_report_path(tmp_path: Path) -> None:
    """The manifest is written to the requested path with schema + stats."""
    manifest_path = tmp_path / "compiled" / "manifest.json"

    compile_identity_vector_library(
        profile_keys=["tesla"],
        write_manifest=True,
        manifest_path=manifest_path,
        compile_func=_make_fake_compile(tmp_path / "art"),
    )

    assert manifest_path.is_file()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == COMPILED_MANIFEST_SCHEMA
    assert payload["successful_count"] == 1
    assert "storage_reduction_percent" in payload
    assert "elapsed_seconds" in payload
    assert "profiles_per_second" in payload


# ---------------------------------------------------------------------------
# Integration against the real single-profile compiler + store
# ---------------------------------------------------------------------------


def _setup_real_compiler(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Point the real compiler at a temp library and isolated work dir."""
    library_dir = tmp_path / "library"
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    monkeypatch.setattr(
        identity_vector_compiler, "LIBRARY_DIR", library_dir
    )
    monkeypatch.setattr(
        identity_vector_compiler,
        "build_raw_vectors_from_acf",
        _fake_raw_vectors,
    )
    # Artifacts write to the default CWD-relative output/ tree.
    monkeypatch.chdir(work_dir)
    return library_dir


def test_integration_rebuild_then_reuse_then_force(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """First run rebuilds, second reuses, --force rebuilds again."""
    library_dir = _setup_real_compiler(tmp_path, monkeypatch)
    _write_acf(library_dir, "nikola_tesla", "Nikola Tesla")
    _write_acf(library_dir, "ada_lovelace", "Ada Lovelace")

    first = compile_identity_vector_library(
        library_dir=library_dir, write_manifest=False
    )
    assert first.manifest.requested_count == 2
    assert first.manifest.rebuilt_count == 2
    assert first.manifest.reused_count == 0
    assert first.manifest.total_vector_count == 2 * EXPECTED_VECTOR_COUNT

    second = compile_identity_vector_library(
        library_dir=library_dir, write_manifest=False
    )
    assert second.manifest.rebuilt_count == 0
    assert second.manifest.reused_count == 2

    forced = compile_identity_vector_library(
        library_dir=library_dir, force=True, write_manifest=False
    )
    assert forced.manifest.rebuilt_count == 2
    assert forced.manifest.reused_count == 0


def test_integration_deterministic_artifact_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Artifact paths are stable across runs and match the store."""
    library_dir = _setup_real_compiler(tmp_path, monkeypatch)
    _write_acf(library_dir, "nikola_tesla", "Nikola Tesla")

    first = compile_identity_vector_library(
        library_dir=library_dir, write_manifest=False
    )
    second = compile_identity_vector_library(
        library_dir=library_dir, write_manifest=False
    )

    path_first = first.outcomes[0].output_path
    path_second = second.outcomes[0].output_path
    expected = str(artifact_path_for_profile("nikola_tesla"))

    assert path_first == path_second == expected


def test_integration_source_content_change_triggers_rebuild(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A same-size content change (new hash) forces a rebuild."""
    library_dir = _setup_real_compiler(tmp_path, monkeypatch)
    acf = _write_acf(library_dir, "p", "AAAA")

    compile_identity_vector_library(
        library_dir=library_dir, write_manifest=False
    )

    # Same byte length, different content -> same size, different SHA-256.
    acf.write_text(
        json.dumps({"identity": {"name": "BBBB"}}), encoding="utf-8"
    )

    rerun = compile_identity_vector_library(
        library_dir=library_dir, write_manifest=False
    )
    assert rerun.manifest.rebuilt_count == 1
    assert rerun.manifest.reused_count == 0


def test_integration_source_size_change_triggers_rebuild(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A change in source size forces a rebuild."""
    library_dir = _setup_real_compiler(tmp_path, monkeypatch)
    acf = _write_acf(library_dir, "p", "Nikola Tesla")

    compile_identity_vector_library(
        library_dir=library_dir, write_manifest=False
    )

    acf.write_text(
        json.dumps({"identity": {"name": "A much longer profile name"}}),
        encoding="utf-8",
    )

    rerun = compile_identity_vector_library(
        library_dir=library_dir, write_manifest=False
    )
    assert rerun.manifest.rebuilt_count == 1


def test_integration_unsupported_schema_is_regenerated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An old/unknown-schema artifact is safely rebuilt from the ACF."""
    library_dir = _setup_real_compiler(tmp_path, monkeypatch)
    _write_acf(library_dir, "p", "Nikola Tesla")

    stale_path = artifact_path_for_profile("p")
    stale_path.parent.mkdir(parents=True, exist_ok=True)
    stale_path.write_text(
        json.dumps({"schema_version": "atlas.compiled.identity-vectors.v1"}),
        encoding="utf-8",
    )

    result = compile_identity_vector_library(
        library_dir=library_dir, write_manifest=False
    )
    assert result.manifest.rebuilt_count == 1
    assert result.manifest.successful_count == 1

    # The rebuilt artifact is now valid schema-v2.
    payload = json.loads(stale_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == COMPILED_IDENTITY_VECTOR_SCHEMA


def test_integration_damaged_artifact_is_regenerated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A corrupt artifact file is safely rebuilt from the ACF."""
    library_dir = _setup_real_compiler(tmp_path, monkeypatch)
    _write_acf(library_dir, "p", "Nikola Tesla")

    damaged_path = artifact_path_for_profile("p")
    damaged_path.parent.mkdir(parents=True, exist_ok=True)
    damaged_path.write_text("{ this is not valid json", encoding="utf-8")

    result = compile_identity_vector_library(
        library_dir=library_dir, write_manifest=False
    )
    assert result.manifest.rebuilt_count == 1
    payload = json.loads(damaged_path.read_text(encoding="utf-8"))
    assert payload["vector_count"] == EXPECTED_VECTOR_COUNT


def test_integration_missing_acf_is_a_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A profile whose ACF is missing is reported as a failure."""
    library_dir = _setup_real_compiler(tmp_path, monkeypatch)
    library_dir.mkdir(parents=True, exist_ok=True)

    result = compile_identity_vector_library(
        profile_keys=["ghost_profile"], write_manifest=False
    )

    assert result.manifest.failed_count == 1
    assert result.manifest.failures[0]["profile_key"] == "ghost_profile"
    assert result.manifest.failures[0]["error_type"] == "FileNotFoundError"
