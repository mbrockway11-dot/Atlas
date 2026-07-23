"""Tests for consolidated calibration artifacts and precomputed statistics."""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from atlas.compiled.calibration import (
    CALIBRATION_STATISTICS_SCHEMA,
    CALIBRATION_VECTORS_SCHEMA,
    CalibrationStatisticsArtifact,
    CalibrationVectorArtifact,
    build_calibration_statistics,
    build_calibration_vector_artifact,
    build_feature_statistics,
    compiled_profile_keys,
    group_key,
    load_calibration_statistics,
    load_calibration_vectors,
    load_calibration_vectors_from_artifacts,
    normalize_feature_from_statistics,
    save_calibration_statistics,
    save_calibration_vectors,
    source_manifest_hash,
)
from atlas.compiled.identity_vector_artifact import (
    COMPILED_IDENTITY_VECTOR_SCHEMA,
    CompiledIdentityVectorArtifact,
)
from atlas.compiled.identity_vector_store import save_compiled_identity_vector
from atlas.ive.normalizer import normalize_feature_value
from atlas.ive.schema import VECTOR_FEATURES, PlanetFeatureVector
from compiled_factories import make_artifact


NORMALIZATION_MODES = ("raw", "percentile", "minmax", "zscore")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _vector(
    *,
    name: str,
    cipher: str = "ordinal",
    planet: str = "sun",
    features: dict[str, float] | None = None,
) -> PlanetFeatureVector:
    """Build a planet feature vector carrying the full feature schema."""
    resolved = features or {feature: 0.5 for feature in VECTOR_FEATURES}

    return PlanetFeatureVector(
        version="test",
        name=name,
        cipher=cipher,
        planet=planet,
        kamea=planet,
        grid_size=6,
        features={
            feature: float(resolved.get(feature, 0.5))
            for feature in VECTOR_FEATURES
        },
    )


def _artifact(
    profile_key: str,
    vectors: tuple[PlanetFeatureVector, ...],
    *,
    source_hash: str | None = None,
) -> CompiledIdentityVectorArtifact:
    """Build a compiled artifact around a set of vectors."""
    return make_artifact(
        profile_key,
        vectors,
        source_acf_sha256=source_hash or (profile_key * 64)[:64],
        source_acf_size_bytes=2_048,
        source_acf_path=f"library/{profile_key}/profile.acf.json",
    )


def _random_population(
    seed: int,
    size: int,
) -> list[PlanetFeatureVector]:
    """Build a random but reproducible calibration population."""
    rng = random.Random(seed)

    return [
        _vector(
            name=f"profile_{index}",
            features={
                feature: rng.random() for feature in VECTOR_FEATURES
            },
        )
        for index in range(size)
    ]


# ---------------------------------------------------------------------------
# Feature statistics
# ---------------------------------------------------------------------------


def test_feature_statistics_summarizes_distribution() -> None:
    """Summary moments and quartiles describe the supplied values."""
    statistics = build_feature_statistics([4.0, 1.0, 3.0, 2.0])

    assert statistics.count == 4
    assert statistics.minimum == 1.0
    assert statistics.maximum == 4.0
    assert statistics.mean == 2.5
    assert statistics.median == 2.5
    assert statistics.q1 == 1.5
    assert statistics.q3 == 3.5
    assert statistics.iqr == 2.0
    assert statistics.sorted_values == (1.0, 2.0, 3.0, 4.0)


def test_feature_statistics_rejects_empty_distribution() -> None:
    """An empty distribution has no meaningful summary."""
    with pytest.raises(ValueError):
        build_feature_statistics([])


def test_statistics_group_by_cipher_and_planet() -> None:
    """Normalization groups are keyed by cipher x planet."""
    vectors = [
        _vector(name="a", cipher="ordinal", planet="sun"),
        _vector(name="b", cipher="ordinal", planet="moon"),
        _vector(name="c", cipher="reduction", planet="sun"),
    ]

    statistics = build_calibration_statistics(vectors)

    assert set(statistics.groups) == {
        group_key("ordinal", "sun"),
        group_key("ordinal", "moon"),
        group_key("reduction", "sun"),
    }
    assert statistics.vector_count == 3


# ---------------------------------------------------------------------------
# Numerical parity with the vector-based normalizer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", NORMALIZATION_MODES)
def test_statistics_normalization_matches_vector_path_exactly(
    mode: str,
) -> None:
    """Statistics-driven normalization is bit-identical to the corpus path."""
    population = _random_population(seed=17, size=120)
    statistics = build_calibration_statistics(population)

    probe = random.Random(99)

    for _ in range(50):
        vector = probe.choice(population)

        for feature in VECTOR_FEATURES:
            value = vector.features[feature]

            expected = normalize_feature_value(
                value=value,
                feature=feature,
                calibration_vectors=population,
                mode=mode,
            )
            actual = normalize_feature_from_statistics(
                value=value,
                statistics=statistics.statistics_for(
                    cipher=vector.cipher,
                    planet=vector.planet,
                    feature=feature,
                ),
                mode=mode,
            )

            assert actual == expected


@pytest.mark.parametrize("mode", NORMALIZATION_MODES)
def test_statistics_normalization_matches_for_unseen_values(
    mode: str,
) -> None:
    """Parity holds for values outside the calibration population."""
    population = _random_population(seed=23, size=80)
    statistics = build_calibration_statistics(population)
    feature = VECTOR_FEATURES[0]

    for value in (-2.0, 0.0, 0.25, 0.5, 1.0, 3.0):
        expected = normalize_feature_value(
            value=value,
            feature=feature,
            calibration_vectors=population,
            mode=mode,
        )
        actual = normalize_feature_from_statistics(
            value=value,
            statistics=statistics.statistics_for(
                cipher="ordinal",
                planet="sun",
                feature=feature,
            ),
            mode=mode,
        )

        assert actual == expected


def test_normalization_rejects_unknown_mode() -> None:
    """An unrecognized mode is an error, not a silent passthrough."""
    statistics = build_feature_statistics([0.1, 0.2])

    with pytest.raises(ValueError):
        normalize_feature_from_statistics(
            value=0.15,
            statistics=statistics,
            mode="bogus",
        )


@pytest.mark.parametrize("mode", ("percentile", "minmax", "zscore"))
def test_missing_group_falls_back_to_self_calibration(mode: str) -> None:
    """An absent group yields 0.5, matching self-calibration."""
    assert (
        normalize_feature_from_statistics(
            value=0.87,
            statistics=None,
            mode=mode,
        )
        == 0.5
    )


def test_missing_group_clamps_in_raw_mode() -> None:
    """Raw mode needs no population and simply clamps."""
    assert (
        normalize_feature_from_statistics(
            value=1.4,
            statistics=None,
            mode="raw",
        )
        == 1.0
    )


# ---------------------------------------------------------------------------
# Source manifest hashing
# ---------------------------------------------------------------------------


def test_source_manifest_hash_is_order_independent() -> None:
    """The corpus hash does not depend on iteration order."""
    forward = source_manifest_hash([("a", "1" * 64), ("b", "2" * 64)])
    reverse = source_manifest_hash([("b", "2" * 64), ("a", "1" * 64)])

    assert forward == reverse


def test_source_manifest_hash_detects_corpus_change() -> None:
    """Changed, added, and removed profiles all change the hash."""
    baseline = source_manifest_hash([("a", "1" * 64), ("b", "2" * 64)])

    changed = source_manifest_hash([("a", "1" * 64), ("b", "3" * 64)])
    added = source_manifest_hash(
        [("a", "1" * 64), ("b", "2" * 64), ("c", "4" * 64)]
    )
    removed = source_manifest_hash([("a", "1" * 64)])

    assert len({baseline, changed, added, removed}) == 4


# ---------------------------------------------------------------------------
# Consolidation from compiled artifacts
# ---------------------------------------------------------------------------


def test_consolidates_compiled_artifacts(tmp_path: Path) -> None:
    """The calibration corpus is assembled from compiled artifacts."""
    for index, key in enumerate(("tesla", "newton")):
        save_compiled_identity_vector(
            _artifact(
                key,
                (
                    _vector(name=key, planet="sun"),
                    _vector(name=key, planet="moon"),
                ),
                source_hash=str(index) * 64,
            ),
            output_path=tmp_path / f"{key}.identity-vector.json",
        )

    corpus = build_calibration_vector_artifact(artifact_dir=tmp_path)

    assert corpus.schema_version == CALIBRATION_VECTORS_SCHEMA
    assert corpus.profile_count == 2
    assert corpus.vector_count == 4
    assert corpus.profile_keys == ("newton", "tesla")
    assert corpus.feature_schema == tuple(VECTOR_FEATURES)
    assert len(corpus.source_manifest_hash) == 64


def test_consolidation_skips_damaged_artifacts(tmp_path: Path) -> None:
    """One unreadable artifact never aborts consolidation."""
    save_compiled_identity_vector(
        _artifact("tesla", (_vector(name="tesla"),)),
        output_path=tmp_path / "tesla.identity-vector.json",
    )
    (tmp_path / "broken.identity-vector.json").write_text(
        "{not json",
        encoding="utf-8",
    )

    corpus = build_calibration_vector_artifact(artifact_dir=tmp_path)

    assert corpus.profile_keys == ("tesla",)
    assert compiled_profile_keys(artifact_dir=tmp_path) == (
        "broken",
        "tesla",
    )


def test_load_vectors_from_artifacts(tmp_path: Path) -> None:
    """Calibration vectors load straight from compiled artifacts."""
    save_compiled_identity_vector(
        _artifact(
            "tesla",
            (_vector(name="tesla"), _vector(name="tesla", planet="moon")),
        ),
        output_path=tmp_path / "tesla.identity-vector.json",
    )

    vectors = load_calibration_vectors_from_artifacts(artifact_dir=tmp_path)

    assert len(vectors) == 2
    assert {vector.planet for vector in vectors} == {"sun", "moon"}


def test_compiled_profile_keys_on_missing_directory(tmp_path: Path) -> None:
    """A missing artifact directory yields no keys rather than raising."""
    assert compiled_profile_keys(artifact_dir=tmp_path / "absent") == ()


# ---------------------------------------------------------------------------
# Persistence round-trips
# ---------------------------------------------------------------------------


def test_calibration_vectors_round_trip(tmp_path: Path) -> None:
    """The consolidated corpus survives a save/load cycle exactly."""
    save_compiled_identity_vector(
        _artifact("tesla", (_vector(name="tesla"),)),
        output_path=tmp_path / "tesla.identity-vector.json",
    )

    corpus = build_calibration_vector_artifact(artifact_dir=tmp_path)
    path = save_calibration_vectors(
        corpus,
        output_path=tmp_path / "raw-vectors.json",
    )
    restored = load_calibration_vectors(input_path=path)

    assert restored.vectors == corpus.vectors
    assert restored.source_manifest_hash == corpus.source_manifest_hash
    assert path.read_text(encoding="utf-8").endswith("\n")


def test_statistics_round_trip_preserves_values(tmp_path: Path) -> None:
    """Statistics survive a save/load cycle without drift."""
    statistics = build_calibration_statistics(
        _random_population(seed=5, size=40),
        source_manifest_hash_value="f" * 64,
        profile_count=40,
    )

    path = save_calibration_statistics(
        statistics,
        output_path=tmp_path / "feature-statistics.json",
    )
    restored = load_calibration_statistics(input_path=path)

    assert restored.source_manifest_hash == "f" * 64
    assert restored.profile_count == 40
    assert restored.groups.keys() == statistics.groups.keys()

    for group, features in statistics.groups.items():
        for feature, expected in features.items():
            assert restored.groups[group][feature] == expected


def test_statistics_round_trip_preserves_normalization(
    tmp_path: Path,
) -> None:
    """Reloaded statistics normalize identically to in-memory ones."""
    population = _random_population(seed=31, size=60)
    statistics = build_calibration_statistics(population)

    path = save_calibration_statistics(
        statistics,
        output_path=tmp_path / "stats.json",
    )
    restored = load_calibration_statistics(input_path=path)

    for mode in NORMALIZATION_MODES:
        for feature in VECTOR_FEATURES:
            value = population[0].features[feature]

            assert normalize_feature_from_statistics(
                value=value,
                statistics=restored.statistics_for(
                    cipher="ordinal",
                    planet="sun",
                    feature=feature,
                ),
                mode=mode,
            ) == normalize_feature_from_statistics(
                value=value,
                statistics=statistics.statistics_for(
                    cipher="ordinal",
                    planet="sun",
                    feature=feature,
                ),
                mode=mode,
            )


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def test_calibration_vectors_reject_unsupported_schema() -> None:
    """A foreign calibration schema is rejected rather than guessed at."""
    payload = {
        "schema_version": "atlas.compiled.calibration-vectors.v99",
        "artifact_schema_version": COMPILED_IDENTITY_VECTOR_SCHEMA,
        "source_manifest_hash": "0" * 64,
        "compiler": {
            "name": "x",
            "version": "1",
            "git_commit": "abc",
            "generated_at": "now",
        },
        "feature_schema": list(VECTOR_FEATURES),
        "profile_count": 0,
        "vector_count": 0,
        "profile_keys": [],
        "vectors": [],
    }

    with pytest.raises(ValueError, match="Unsupported calibration schema"):
        CalibrationVectorArtifact.from_dict(payload)


def test_calibration_vectors_reject_count_mismatch() -> None:
    """A declared count that disagrees with the payload is rejected."""
    corpus = CalibrationVectorArtifact(
        schema_version=CALIBRATION_VECTORS_SCHEMA,
        artifact_schema_version=COMPILED_IDENTITY_VECTOR_SCHEMA,
        source_manifest_hash="0" * 64,
        compiler_name="x",
        compiler_version="1",
        compiler_git_commit="abc",
        feature_schema_hash="0" * 64,
        generated_at="now",
        feature_schema=tuple(VECTOR_FEATURES),
        profile_count=1,
        vector_count=1,
        profile_keys=("tesla",),
        vectors=(_vector(name="tesla"),),
    )

    payload = corpus.to_dict()
    payload["vector_count"] = 7

    with pytest.raises(ValueError, match="vector count mismatch"):
        CalibrationVectorArtifact.from_dict(payload)


def test_statistics_reject_unsupported_schema() -> None:
    """A foreign statistics schema is rejected."""
    statistics = build_calibration_statistics([_vector(name="a")])
    payload = statistics.to_dict()
    payload["schema_version"] = "atlas.compiled.calibration-statistics.v99"

    with pytest.raises(ValueError, match="Unsupported calibration"):
        CalibrationStatisticsArtifact.from_dict(payload)


def test_statistics_reject_non_object_root(tmp_path: Path) -> None:
    """A JSON array is not a valid statistics document."""
    path = tmp_path / "stats.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    with pytest.raises(ValueError, match="must be an object"):
        load_calibration_statistics(input_path=path)
