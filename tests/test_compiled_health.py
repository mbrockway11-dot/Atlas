"""Tests for the compiled-runtime health surface.

Health exists to make silent drift visible, so these tests focus on the
cases that still "work" while being wrong: an index or statistics built
against a different feature schema, and statistics pinned to a corpus
revision the index has moved past.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.compiled.calibration import (
    build_calibration_statistics,
    build_calibration_vector_artifact,
    save_calibration_statistics,
)
from atlas.compiled.health import (
    STATUS_ERROR,
    STATUS_MISSING,
    STATUS_OK,
    STATUS_STALE,
    build_runtime_health,
)
from atlas.compiled.identity_vector_store import save_compiled_identity_vector
from atlas.compiled.index import build_compiled_index, save_compiled_index
from atlas.compiled.manifest import (
    build_compilation_manifest,
    save_compilation_manifest,
)
from compiled_factories import make_artifact, make_vector


@pytest.fixture
def runtime(tmp_path: Path) -> dict[str, Path]:
    """Build a complete, healthy compiled runtime on disk."""
    library_dir = tmp_path / "library"
    artifact_dir = tmp_path / "compiled" / "identity_vectors"
    artifact_dir.mkdir(parents=True)

    for profile_key in ("tesla", "newton"):
        profile_dir = library_dir / profile_key
        profile_dir.mkdir(parents=True)
        (profile_dir / "profile.acf.json").write_text(
            json.dumps({"identity": {"name": profile_key.title()}}),
            encoding="utf-8",
        )

        save_compiled_identity_vector(
            make_artifact(
                profile_key,
                (make_vector(name=profile_key, full_schema=True),),
            ),
            output_path=artifact_dir / f"{profile_key}.identity-vector.json",
        )

    manifest_path = tmp_path / "compiled" / "manifest.json"
    save_compilation_manifest(
        build_compilation_manifest(
            requested_count=2,
            successful_count=2,
            rebuilt_count=2,
            reused_count=0,
            failed_count=0,
            total_vector_count=2,
            total_source_bytes=100,
            total_artifact_bytes=10,
        ),
        output_path=manifest_path,
    )

    index_path = tmp_path / "compiled" / "index.json"
    save_compiled_index(
        build_compiled_index(artifact_dir=artifact_dir),
        output_path=index_path,
    )

    corpus = build_calibration_vector_artifact(artifact_dir=artifact_dir)
    statistics_path = tmp_path / "compiled" / "feature-statistics.json"
    save_calibration_statistics(
        build_calibration_statistics(
            corpus.vectors,
            source_manifest_hash_value=corpus.source_manifest_hash,
            profile_count=corpus.profile_count,
        ),
        output_path=statistics_path,
    )

    return {
        "library_dir": library_dir,
        "artifact_dir": artifact_dir,
        "manifest_path": manifest_path,
        "index_path": index_path,
        "statistics_path": statistics_path,
    }


def _health(runtime: dict[str, Path], **overrides):
    """Build health for the fixture runtime."""
    return build_runtime_health(**{**runtime, **overrides})


def test_complete_runtime_is_healthy(runtime: dict[str, Path]) -> None:
    """A freshly built runtime reports OK across every component."""
    health = _health(runtime)

    assert health.status == STATUS_OK
    assert health.healthy is True
    assert health.problems() == ()
    assert {c.name for c in health.components} == {
        "manifest",
        "artifacts",
        "index",
        "statistics",
    }


def test_health_reports_schema_and_compiler_identity(
    runtime: dict[str, Path],
) -> None:
    """The report states what the runtime currently is."""
    health = _health(runtime)
    payload = health.to_dict()

    assert payload["artifact_schema_version"].endswith(".v3")
    assert payload["compiler_version"]
    assert len(payload["feature_schema_hash"]) == 64


def test_deep_check_validates_against_sources(
    runtime: dict[str, Path],
) -> None:
    """Deep mode reports stale counts rather than only presence."""
    health = _health(runtime, deep=True)
    artifacts = next(c for c in health.components if c.name == "artifacts")

    assert artifacts.data["deep"] is True
    assert "stale_count" in artifacts.data
    assert "damaged_count" in artifacts.data


def test_missing_manifest_is_reported(runtime: dict[str, Path]) -> None:
    """An absent manifest is missing, not an error."""
    runtime["manifest_path"].unlink()

    health = _health(runtime)
    manifest = next(c for c in health.components if c.name == "manifest")

    assert manifest.status == STATUS_MISSING
    assert health.status == STATUS_MISSING
    assert not health.healthy


def test_missing_statistics_is_reported(runtime: dict[str, Path]) -> None:
    """Absent statistics are surfaced with the command that builds them."""
    runtime["statistics_path"].unlink()

    statistics = next(
        c for c in _health(runtime).components if c.name == "statistics"
    )

    assert statistics.status == STATUS_MISSING
    assert "build_calibration_statistics" in statistics.detail


def test_failed_profiles_make_manifest_stale(runtime: dict[str, Path]) -> None:
    """Recorded compile failures are surfaced, not averaged away."""
    save_compilation_manifest(
        build_compilation_manifest(
            requested_count=3,
            successful_count=2,
            rebuilt_count=2,
            reused_count=0,
            failed_count=1,
            total_vector_count=2,
            total_source_bytes=100,
            total_artifact_bytes=10,
            failures=({"profile_key": "broken", "error": "no ACF"},),
        ),
        output_path=runtime["manifest_path"],
    )

    manifest = next(
        c for c in _health(runtime).components if c.name == "manifest"
    )

    assert manifest.status == STATUS_STALE
    assert manifest.data["failed_count"] == 1


def test_foreign_feature_schema_marks_index_stale(
    runtime: dict[str, Path],
) -> None:
    """An index built against another feature schema is stale."""
    payload = json.loads(runtime["index_path"].read_text(encoding="utf-8"))
    payload["feature_schema_hash"] = "0" * 64
    runtime["index_path"].write_text(json.dumps(payload), encoding="utf-8")

    index = next(c for c in _health(runtime).components if c.name == "index")

    assert index.status == STATUS_STALE
    assert "feature schema" in index.detail


def test_foreign_feature_schema_marks_statistics_stale(
    runtime: dict[str, Path],
) -> None:
    """Statistics built against another feature schema are stale."""
    payload = json.loads(
        runtime["statistics_path"].read_text(encoding="utf-8")
    )
    payload["feature_schema_hash"] = "0" * 64
    runtime["statistics_path"].write_text(
        json.dumps(payload), encoding="utf-8"
    )

    statistics = next(
        c for c in _health(runtime).components if c.name == "statistics"
    )

    assert statistics.status == STATUS_STALE
    assert "feature schema" in statistics.detail


def test_statistics_from_a_different_corpus_are_stale(
    runtime: dict[str, Path],
) -> None:
    """Statistics must describe the corpus the index reflects.

    This is the quiet failure: normalization keeps working but calibrates
    against a population that no longer matches the corpus.
    """
    payload = json.loads(
        runtime["statistics_path"].read_text(encoding="utf-8")
    )
    payload["source_manifest_hash"] = "9" * 64
    runtime["statistics_path"].write_text(
        json.dumps(payload), encoding="utf-8"
    )

    statistics = next(
        c for c in _health(runtime).components if c.name == "statistics"
    )

    assert statistics.status == STATUS_STALE
    assert "corpus revision" in statistics.detail


def test_unreadable_index_is_an_error(runtime: dict[str, Path]) -> None:
    """A corrupt index is an error, distinct from a missing one."""
    runtime["index_path"].write_text("{not json", encoding="utf-8")

    health = _health(runtime)
    index = next(c for c in health.components if c.name == "index")

    assert index.status == STATUS_ERROR
    assert health.status == STATUS_ERROR


def test_missing_artifacts_are_counted(runtime: dict[str, Path]) -> None:
    """A profile with a source but no artifact is reported."""
    (runtime["artifact_dir"] / "tesla.identity-vector.json").unlink()

    artifacts = next(
        c for c in _health(runtime).components if c.name == "artifacts"
    )

    assert artifacts.status == STATUS_STALE
    assert artifacts.data["missing_count"] == 1
    assert "tesla" in artifacts.data["missing_sample"]


def test_problems_are_ordered_worst_first(runtime: dict[str, Path]) -> None:
    """Triage order puts errors above merely-missing components."""
    runtime["manifest_path"].unlink()
    runtime["index_path"].write_text("{not json", encoding="utf-8")

    problems = _health(runtime).problems()

    assert problems[0].status == STATUS_ERROR
    assert {p.name for p in problems} >= {"manifest", "index"}
