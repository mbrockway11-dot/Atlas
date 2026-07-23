"""Numerical parity between the ACF path and the compiled runtime.

The compiled layer is only safe to make authoritative at runtime if it
reproduces the old ACF-driven results exactly. These tests compile a small
real corpus and assert that raw vectors, normalized features, identity
comparisons, ranking order, and feature contributions all match.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from atlas.acf.builder import build_acf_profile
from atlas.compiled import identity_vector_compiler
from atlas.compiled.calibration import build_calibration_statistics
from atlas.compiled.identity_vector_compiler import (
    compile_identity_vector_artifact,
)
from atlas.compiled.runtime import (
    CompiledRuntimeError,
    build_runtime_identity_vector,
    clear_runtime_caches,
    load_runtime_artifact,
    normalize_vectors_with_statistics,
    runtime_provenance,
)
from atlas.ive import (
    build_identity_vector,
    build_raw_vectors_from_acf,
    compare_identity_vectors,
)
from atlas.ive.normalizer import normalize_planet_vectors


NORMALIZATION_MODES = ("raw", "percentile", "minmax", "zscore")

PROFILE_NAMES = {
    "nikola_tesla": "Nikola Tesla",
    "isaac_newton": "Isaac Newton",
    "ada_lovelace": "Ada Lovelace",
    "marie_curie": "Marie Curie",
    "alan_turing": "Alan Turing",
    "grace_hopper": "Grace Hopper",
}


class _Corpus:
    """A compiled corpus plus the ACFs it was compiled from."""

    def __init__(
        self,
        acfs: dict[str, dict],
        artifacts: dict[str, object],
    ) -> None:
        self.acfs = acfs
        self.artifacts = artifacts
        self.keys = tuple(sorted(acfs))

        self.calibration_acfs = [acfs[key] for key in self.keys]
        self.calibration_vectors = [
            vector
            for key in self.keys
            for vector in self.artifacts[key].vectors
        ]
        self.statistics = build_calibration_statistics(
            self.calibration_vectors,
            profile_count=len(self.keys),
        )


@pytest.fixture(scope="module")
def corpus(tmp_path_factory: pytest.TempPathFactory) -> _Corpus:
    """Build and compile a small real corpus once for the module."""
    tmp_path = tmp_path_factory.mktemp("parity")
    library_dir = tmp_path / "library"
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    acfs: dict[str, dict] = {}

    for profile_key, name in PROFILE_NAMES.items():
        acf = build_acf_profile(name)
        profile_dir = library_dir / profile_key
        profile_dir.mkdir(parents=True, exist_ok=True)

        (profile_dir / "profile.acf.json").write_text(
            json.dumps(acf),
            encoding="utf-8",
        )
        acfs[profile_key] = acf

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(identity_vector_compiler, "LIBRARY_DIR", library_dir)
        patch.chdir(work_dir)

        artifacts = {
            profile_key: compile_identity_vector_artifact(profile_key)[0]
            for profile_key in acfs
        }

    return _Corpus(acfs, artifacts)


@pytest.fixture
def runtime_library(
    corpus: _Corpus,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Point the runtime at an isolated copy of the compiled corpus."""
    library_dir = tmp_path / "library"
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    for profile_key, acf in corpus.acfs.items():
        profile_dir = library_dir / profile_key
        profile_dir.mkdir(parents=True, exist_ok=True)
        (profile_dir / "profile.acf.json").write_text(
            json.dumps(acf),
            encoding="utf-8",
        )

    monkeypatch.setattr(identity_vector_compiler, "LIBRARY_DIR", library_dir)
    monkeypatch.chdir(work_dir)
    clear_runtime_caches()

    yield library_dir

    clear_runtime_caches()


def _legacy_identity_vector(corpus: _Corpus, profile_key: str, mode: str):
    """Build an identity vector the old way, from calibration ACFs."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        return build_identity_vector(
            acf=corpus.acfs[profile_key],
            calibration_acfs=corpus.calibration_acfs,
            normalization_mode=mode,
        )


# ---------------------------------------------------------------------------
# Vector-level parity
# ---------------------------------------------------------------------------


def test_compiled_vectors_match_fresh_acf_vectors(corpus: _Corpus) -> None:
    """Compiled artifacts preserve raw vectors exactly."""
    for profile_key in corpus.keys:
        fresh = build_raw_vectors_from_acf(corpus.acfs[profile_key])
        compiled = list(corpus.artifacts[profile_key].vectors)

        assert compiled == fresh


def test_compiled_corpus_has_expected_shape(corpus: _Corpus) -> None:
    """Every profile compiles to the nominal 21 vectors."""
    for profile_key in corpus.keys:
        artifact = corpus.artifacts[profile_key]

        assert artifact.vector_count == 21
        assert len(artifact.vectors) == 21


@pytest.mark.parametrize("mode", NORMALIZATION_MODES)
def test_normalized_vectors_match_corpus_path(
    corpus: _Corpus,
    mode: str,
) -> None:
    """Statistics-driven normalization matches corpus normalization."""
    for profile_key in corpus.keys:
        raw = list(corpus.artifacts[profile_key].vectors)

        expected = normalize_planet_vectors(
            vectors=raw,
            calibration_vectors=corpus.calibration_vectors,
            mode=mode,
        )
        actual = normalize_vectors_with_statistics(
            raw,
            corpus.statistics if mode != "raw" else None,
            mode,
        )

        assert len(actual) == len(expected)

        for actual_vector, expected_vector in zip(actual, expected):
            assert actual_vector.features == expected_vector.features
            assert actual_vector.raw_features == expected_vector.raw_features
            assert actual_vector.planet == expected_vector.planet
            assert actual_vector.cipher == expected_vector.cipher

            if mode != "raw":
                assert (
                    actual_vector.calibration_size
                    == expected_vector.calibration_size
                )


# ---------------------------------------------------------------------------
# Identity-vector parity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", NORMALIZATION_MODES)
def test_identity_vectors_match_legacy_path(
    corpus: _Corpus,
    runtime_library: Path,
    mode: str,
) -> None:
    """Compiled-runtime identity vectors equal the ACF-built ones."""
    for profile_key in corpus.keys:
        expected = _legacy_identity_vector(corpus, profile_key, mode)
        actual, artifact = build_runtime_identity_vector(
            profile_key,
            normalization_mode=mode,
            statistics=corpus.statistics,
        )

        assert artifact.profile_key == profile_key
        assert actual.name == expected.name
        assert actual.global_features == expected.global_features
        assert actual.diagnostics == expected.diagnostics
        assert actual.planets.keys() == expected.planets.keys()

        for planet, planet_vector in expected.planets.items():
            assert actual.planets[planet].features == planet_vector.features


# ---------------------------------------------------------------------------
# Comparison parity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", NORMALIZATION_MODES)
def test_comparison_output_matches_legacy_path(
    corpus: _Corpus,
    runtime_library: Path,
    mode: str,
) -> None:
    """Whole comparison payloads match, including feature contributions."""
    key_a, key_b = corpus.keys[0], corpus.keys[1]

    expected = compare_identity_vectors(
        _legacy_identity_vector(corpus, key_a, mode),
        _legacy_identity_vector(corpus, key_b, mode),
    )
    actual = compare_identity_vectors(
        build_runtime_identity_vector(
            key_a,
            normalization_mode=mode,
            statistics=corpus.statistics,
        )[0],
        build_runtime_identity_vector(
            key_b,
            normalization_mode=mode,
            statistics=corpus.statistics,
        )[0],
    )

    assert actual.composite_similarity == expected.composite_similarity
    assert actual.global_similarity == expected.global_similarity
    assert (
        actual.relationship_similarity == expected.relationship_similarity
    )
    assert actual.global_distance == expected.global_distance
    assert actual.diagnostics == expected.diagnostics


@pytest.mark.parametrize("mode", NORMALIZATION_MODES)
def test_ranking_order_is_unchanged(
    corpus: _Corpus,
    runtime_library: Path,
    mode: str,
) -> None:
    """Ranking every profile against a pivot yields the same order."""
    pivot = corpus.keys[0]
    others = corpus.keys[1:]

    legacy_pivot = _legacy_identity_vector(corpus, pivot, mode)
    runtime_pivot = build_runtime_identity_vector(
        pivot,
        normalization_mode=mode,
        statistics=corpus.statistics,
    )[0]

    legacy_ranking = sorted(
        (
            (
                compare_identity_vectors(
                    legacy_pivot,
                    _legacy_identity_vector(corpus, key, mode),
                ).composite_similarity,
                key,
            )
            for key in others
        ),
        reverse=True,
    )

    runtime_ranking = sorted(
        (
            (
                compare_identity_vectors(
                    runtime_pivot,
                    build_runtime_identity_vector(
                        key,
                        normalization_mode=mode,
                        statistics=corpus.statistics,
                    )[0],
                ).composite_similarity,
                key,
            )
            for key in others
        ),
        reverse=True,
    )

    assert runtime_ranking == legacy_ranking
    assert [key for _, key in runtime_ranking] == [
        key for _, key in legacy_ranking
    ]


# ---------------------------------------------------------------------------
# Runtime resolution behaviour
# ---------------------------------------------------------------------------


def test_runtime_compiles_missing_artifact(
    corpus: _Corpus,
    runtime_library: Path,
) -> None:
    """A profile with no artifact yet is compiled on demand."""
    artifact = load_runtime_artifact("nikola_tesla")

    assert artifact.profile_key == "nikola_tesla"
    assert artifact.vector_count == 21


def test_runtime_rebuilds_when_source_changes(
    corpus: _Corpus,
    runtime_library: Path,
) -> None:
    """Editing the source ACF invalidates the cached artifact."""
    first = load_runtime_artifact("nikola_tesla")

    acf_path = runtime_library / "nikola_tesla" / "profile.acf.json"
    replacement = build_acf_profile("Ada Lovelace")
    acf_path.write_text(json.dumps(replacement), encoding="utf-8")

    second = load_runtime_artifact("nikola_tesla")

    assert second.source_acf_sha256 != first.source_acf_sha256
    assert second.profile_name == "Ada Lovelace"


def test_runtime_cache_returns_same_artifact(
    corpus: _Corpus,
    runtime_library: Path,
) -> None:
    """An unchanged source serves the cached artifact object."""
    first = load_runtime_artifact("nikola_tesla")
    second = load_runtime_artifact("nikola_tesla")

    assert second is first

    clear_runtime_caches()

    assert load_runtime_artifact("nikola_tesla") is not first


def test_runtime_reports_controlled_error_for_unknown_profile(
    corpus: _Corpus,
    runtime_library: Path,
) -> None:
    """An unresolvable profile raises a controlled runtime error."""
    with pytest.raises(CompiledRuntimeError, match="does_not_exist"):
        load_runtime_artifact("does_not_exist")


def test_runtime_provenance_reports_source_revision(
    corpus: _Corpus,
    runtime_library: Path,
) -> None:
    """Provenance identifies the compiler and source revision."""
    artifact = load_runtime_artifact("nikola_tesla")
    provenance = runtime_provenance(artifact)

    assert provenance["profile_key"] == "nikola_tesla"
    assert provenance["vector_count"] == 21
    assert len(provenance["source_acf_sha256"]) == 64
    assert provenance["schema_version"].endswith(".v2")


def test_raw_mode_needs_no_statistics(
    corpus: _Corpus,
    runtime_library: Path,
) -> None:
    """Raw comparisons never touch the calibration layer."""
    vector, _ = build_runtime_identity_vector(
        "nikola_tesla",
        normalization_mode="raw",
    )

    assert vector.name == "Nikola Tesla"
