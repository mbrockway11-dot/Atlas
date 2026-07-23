"""Consolidated calibration artifacts for the Atlas compiled runtime.

Two artifacts live here, both derived from the per-profile compiled
identity-vector artifacts:

* ``raw-vectors.json`` -- every calibration vector in the corpus in one
  compact file, so callers load a single document instead of opening
  thousands of individual artifacts (and never the source ACFs).
* ``feature-statistics.json`` -- precomputed per-group, per-feature
  statistics, so a comparison never has to hold the whole calibration
  corpus in memory at all.

Normalization in Atlas happens within a comparable measurement group --
cipher x planet -- so every statistic here is keyed by that group and then
by feature. Statistics carry the exact sorted value distribution alongside
the summary moments because percentile normalization is rank-based and
cannot be reconstructed from moments alone. That keeps the statistics path
numerically identical to the corpus path rather than merely close.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any, Iterable

from atlas.compiled.compiler_identity import build_compiler_identity
from atlas.compiled.identity_vector_artifact import (
    COMPILED_IDENTITY_VECTOR_SCHEMA,
)
from atlas.compiled.identity_vector_store import (
    DEFAULT_COMPILED_VECTOR_DIR,
    load_compiled_identity_vector,
)
from atlas.ive.schema import VECTOR_FEATURES, PlanetFeatureVector


CALIBRATION_VECTORS_SCHEMA = "atlas.compiled.calibration-vectors.v1"
CALIBRATION_STATISTICS_SCHEMA = "atlas.compiled.calibration-statistics.v1"

DEFAULT_CALIBRATION_DIR = Path("output") / "compiled" / "calibration"
DEFAULT_CALIBRATION_VECTORS_PATH = (
    DEFAULT_CALIBRATION_DIR / "raw-vectors.json"
)
DEFAULT_FEATURE_STATISTICS_PATH = (
    DEFAULT_CALIBRATION_DIR / "feature-statistics.json"
)


def group_key(cipher: str, planet: str) -> str:
    """Return the comparable-measurement-group key for a vector."""
    return f"{cipher}|{planet}"


# ---------------------------------------------------------------------------
# Loading compiled vectors
# ---------------------------------------------------------------------------


def iter_compiled_calibration_vectors(
    profile_keys: Iterable[str] | None = None,
    *,
    artifact_dir: Path = DEFAULT_COMPILED_VECTOR_DIR,
    skip_invalid: bool = True,
) -> Iterable[tuple[str, tuple[PlanetFeatureVector, ...]]]:
    """Yield ``(profile_key, vectors)`` from compiled artifacts.

    This is the compiled-runtime replacement for reparsing every ACF. When
    ``profile_keys`` is omitted the artifact directory is scanned.
    """
    if profile_keys is None:
        keys = compiled_profile_keys(artifact_dir=artifact_dir)
    else:
        keys = tuple(
            key.strip() for key in profile_keys if key and key.strip()
        )

    for profile_key in keys:
        path = artifact_dir / f"{profile_key}.identity-vector.json"

        try:
            artifact = load_compiled_identity_vector(input_path=path)
        except (
            FileNotFoundError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ):
            if skip_invalid:
                continue

            raise

        yield profile_key, artifact.vectors


def compiled_profile_keys(
    *,
    artifact_dir: Path = DEFAULT_COMPILED_VECTOR_DIR,
) -> tuple[str, ...]:
    """Return sorted profile keys that have a compiled artifact on disk."""
    if not artifact_dir.is_dir():
        return ()

    suffix = ".identity-vector.json"

    return tuple(
        sorted(
            entry.name[: -len(suffix)]
            for entry in artifact_dir.iterdir()
            if entry.is_file() and entry.name.endswith(suffix)
        )
    )


def load_calibration_vectors_from_artifacts(
    profile_keys: Iterable[str] | None = None,
    *,
    artifact_dir: Path = DEFAULT_COMPILED_VECTOR_DIR,
) -> list[PlanetFeatureVector]:
    """Return every calibration vector read from compiled artifacts."""
    vectors: list[PlanetFeatureVector] = []

    for _, profile_vectors in iter_compiled_calibration_vectors(
        profile_keys,
        artifact_dir=artifact_dir,
    ):
        vectors.extend(profile_vectors)

    return vectors


# ---------------------------------------------------------------------------
# Consolidated calibration corpus
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CalibrationVectorArtifact:
    """Every calibration vector in the corpus, in one document."""

    schema_version: str
    artifact_schema_version: str
    source_manifest_hash: str
    compiler_name: str
    compiler_version: str
    compiler_git_commit: str
    feature_schema_hash: str
    generated_at: str
    feature_schema: tuple[str, ...]
    profile_count: int
    vector_count: int
    profile_keys: tuple[str, ...]
    vectors: tuple[PlanetFeatureVector, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert into JSON-safe primitive values."""
        return {
            "schema_version": self.schema_version,
            "artifact_schema_version": self.artifact_schema_version,
            "source_manifest_hash": self.source_manifest_hash,
            "feature_schema_hash": self.feature_schema_hash,
            "compiler": {
                "name": self.compiler_name,
                "version": self.compiler_version,
                "git_commit": self.compiler_git_commit,
                "generated_at": self.generated_at,
            },
            "feature_schema": list(self.feature_schema),
            "profile_count": self.profile_count,
            "vector_count": self.vector_count,
            "profile_keys": list(self.profile_keys),
            "vectors": [
                {
                    "version": vector.version,
                    "name": vector.name,
                    "cipher": vector.cipher,
                    "planet": vector.planet,
                    "kamea": vector.kamea,
                    "grid_size": vector.grid_size,
                    "features": dict(vector.features),
                }
                for vector in self.vectors
            ],
        }

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "CalibrationVectorArtifact":
        """Reconstruct and validate from decoded JSON."""
        schema_version = str(payload["schema_version"])

        if schema_version != CALIBRATION_VECTORS_SCHEMA:
            raise ValueError(
                f"Unsupported calibration schema: {schema_version!r}"
            )

        compiler = payload["compiler"]

        vectors = tuple(
            PlanetFeatureVector(
                version=str(row["version"]),
                name=str(row["name"]),
                cipher=str(row["cipher"]),
                planet=str(row["planet"]),
                kamea=str(row["kamea"]),
                grid_size=int(row["grid_size"]),
                features={
                    str(feature): float(value)
                    for feature, value in row["features"].items()
                },
            )
            for row in payload["vectors"]
        )

        expected_count = int(payload["vector_count"])

        if len(vectors) != expected_count:
            raise ValueError(
                "Calibration vector count mismatch: expected "
                f"{expected_count}, found {len(vectors)}"
            )

        return cls(
            schema_version=schema_version,
            artifact_schema_version=str(
                payload["artifact_schema_version"]
            ),
            source_manifest_hash=str(payload["source_manifest_hash"]),
            compiler_name=str(compiler["name"]),
            compiler_version=str(compiler["version"]),
            compiler_git_commit=str(compiler["git_commit"]),
            feature_schema_hash=str(payload.get("feature_schema_hash", "")),
            generated_at=str(compiler["generated_at"]),
            feature_schema=tuple(
                str(feature) for feature in payload["feature_schema"]
            ),
            profile_count=int(payload["profile_count"]),
            vector_count=expected_count,
            profile_keys=tuple(
                str(key) for key in payload["profile_keys"]
            ),
            vectors=vectors,
        )


def source_manifest_hash(
    profile_sources: Iterable[tuple[str, str]],
) -> str:
    """Hash the ``(profile_key, source_acf_sha256)`` set of a corpus.

    Ties a derived artifact to the exact corpus revision that produced it,
    so a changed, added, or removed profile invalidates it. Sorting first
    makes the hash independent of iteration order.
    """
    digest = hashlib.sha256()

    for profile_key, source_hash in sorted(profile_sources):
        digest.update(profile_key.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(source_hash.encode("utf-8"))
        digest.update(b"\n")

    return digest.hexdigest()


def build_calibration_vector_artifact(
    *,
    artifact_dir: Path = DEFAULT_COMPILED_VECTOR_DIR,
    profile_keys: Iterable[str] | None = None,
) -> CalibrationVectorArtifact:
    """Consolidate compiled artifacts into one calibration document."""
    if profile_keys is None:
        keys = compiled_profile_keys(artifact_dir=artifact_dir)
    else:
        keys = tuple(
            key.strip() for key in profile_keys if key and key.strip()
        )

    included: list[str] = []
    sources: list[tuple[str, str]] = []
    vectors: list[PlanetFeatureVector] = []

    suffix = ".identity-vector.json"

    for profile_key in keys:
        path = artifact_dir / f"{profile_key}{suffix}"

        try:
            artifact = load_compiled_identity_vector(input_path=path)
        except (
            FileNotFoundError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ):
            continue

        included.append(profile_key)
        sources.append((profile_key, artifact.source_acf_sha256))
        vectors.extend(artifact.vectors)

    compiler = build_compiler_identity()

    return CalibrationVectorArtifact(
        schema_version=CALIBRATION_VECTORS_SCHEMA,
        artifact_schema_version=COMPILED_IDENTITY_VECTOR_SCHEMA,
        source_manifest_hash=source_manifest_hash(sources),
        compiler_name=compiler.name,
        compiler_version=compiler.version,
        compiler_git_commit=compiler.git_commit,
        feature_schema_hash=compiler.feature_schema_hash,
        generated_at=compiler.generated_at,
        feature_schema=tuple(VECTOR_FEATURES),
        profile_count=len(included),
        vector_count=len(vectors),
        profile_keys=tuple(included),
        vectors=tuple(vectors),
    )


# ---------------------------------------------------------------------------
# Precomputed feature statistics
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FeatureStatistics:
    """Distribution of one feature within one comparable group."""

    count: int
    minimum: float
    maximum: float
    mean: float
    stddev: float
    median: float
    q1: float
    q3: float
    sorted_values: tuple[float, ...]

    @property
    def iqr(self) -> float:
        """Return the interquartile range."""
        return self.q3 - self.q1

    def to_dict(self) -> dict[str, Any]:
        """Convert into JSON-safe primitive values."""
        return {
            "count": self.count,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "mean": self.mean,
            "stddev": self.stddev,
            "median": self.median,
            "q1": self.q1,
            "q3": self.q3,
            "iqr": self.iqr,
            "sorted_values": list(self.sorted_values),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "FeatureStatistics":
        """Reconstruct from decoded JSON."""
        return cls(
            count=int(payload["count"]),
            minimum=float(payload["minimum"]),
            maximum=float(payload["maximum"]),
            mean=float(payload["mean"]),
            stddev=float(payload["stddev"]),
            median=float(payload["median"]),
            q1=float(payload["q1"]),
            q3=float(payload["q3"]),
            sorted_values=tuple(
                float(value) for value in payload["sorted_values"]
            ),
        )


def build_feature_statistics(
    values: Iterable[float],
) -> FeatureStatistics:
    """Summarize one feature distribution."""
    ordered = sorted(float(value) for value in values)

    if not ordered:
        raise ValueError("Cannot summarize an empty distribution.")

    count = len(ordered)
    midpoint = count // 2

    lower_half = ordered[:midpoint]
    upper_half = ordered[midpoint + 1 :] if count % 2 else ordered[midpoint:]

    return FeatureStatistics(
        count=count,
        minimum=ordered[0],
        maximum=ordered[-1],
        mean=mean(ordered),
        stddev=pstdev(ordered) if count > 1 else 0.0,
        median=median(ordered),
        q1=median(lower_half) if lower_half else ordered[0],
        q3=median(upper_half) if upper_half else ordered[-1],
        sorted_values=tuple(ordered),
    )


@dataclass(frozen=True, slots=True)
class CalibrationStatisticsArtifact:
    """Per-group, per-feature calibration statistics for the whole corpus."""

    schema_version: str
    artifact_schema_version: str
    source_manifest_hash: str
    compiler_name: str
    compiler_version: str
    compiler_git_commit: str
    feature_schema_hash: str
    generated_at: str
    feature_schema: tuple[str, ...]
    profile_count: int
    vector_count: int
    groups: dict[str, dict[str, FeatureStatistics]]

    def statistics_for(
        self,
        *,
        cipher: str,
        planet: str,
        feature: str,
    ) -> FeatureStatistics | None:
        """Return statistics for one group/feature, or None if absent."""
        return self.groups.get(group_key(cipher, planet), {}).get(feature)

    def to_dict(self) -> dict[str, Any]:
        """Convert into JSON-safe primitive values."""
        return {
            "schema_version": self.schema_version,
            "artifact_schema_version": self.artifact_schema_version,
            "source_manifest_hash": self.source_manifest_hash,
            "feature_schema_hash": self.feature_schema_hash,
            "compiler": {
                "name": self.compiler_name,
                "version": self.compiler_version,
                "git_commit": self.compiler_git_commit,
                "generated_at": self.generated_at,
            },
            "feature_schema": list(self.feature_schema),
            "profile_count": self.profile_count,
            "vector_count": self.vector_count,
            "group_count": len(self.groups),
            "groups": {
                group: {
                    feature: statistics.to_dict()
                    for feature, statistics in features.items()
                }
                for group, features in self.groups.items()
            },
        }

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "CalibrationStatisticsArtifact":
        """Reconstruct and validate from decoded JSON."""
        schema_version = str(payload["schema_version"])

        if schema_version != CALIBRATION_STATISTICS_SCHEMA:
            raise ValueError(
                "Unsupported calibration statistics schema: "
                f"{schema_version!r}"
            )

        compiler = payload["compiler"]

        return cls(
            schema_version=schema_version,
            artifact_schema_version=str(
                payload["artifact_schema_version"]
            ),
            source_manifest_hash=str(payload["source_manifest_hash"]),
            compiler_name=str(compiler["name"]),
            compiler_version=str(compiler["version"]),
            compiler_git_commit=str(compiler["git_commit"]),
            feature_schema_hash=str(payload.get("feature_schema_hash", "")),
            generated_at=str(compiler["generated_at"]),
            feature_schema=tuple(
                str(feature) for feature in payload["feature_schema"]
            ),
            profile_count=int(payload["profile_count"]),
            vector_count=int(payload["vector_count"]),
            groups={
                str(group): {
                    str(feature): FeatureStatistics.from_dict(stats)
                    for feature, stats in features.items()
                }
                for group, features in payload["groups"].items()
            },
        )


def build_calibration_statistics(
    vectors: Iterable[PlanetFeatureVector],
    *,
    source_manifest_hash_value: str = "",
    profile_count: int = 0,
) -> CalibrationStatisticsArtifact:
    """Precompute per-group, per-feature statistics from raw vectors."""
    grouped: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    vector_count = 0

    for vector in vectors:
        vector_count += 1
        bucket = grouped[group_key(vector.cipher, vector.planet)]

        for feature, value in vector.features.items():
            bucket[feature].append(float(value))

    compiler = build_compiler_identity()

    return CalibrationStatisticsArtifact(
        schema_version=CALIBRATION_STATISTICS_SCHEMA,
        artifact_schema_version=COMPILED_IDENTITY_VECTOR_SCHEMA,
        source_manifest_hash=source_manifest_hash_value,
        compiler_name=compiler.name,
        compiler_version=compiler.version,
        compiler_git_commit=compiler.git_commit,
        feature_schema_hash=compiler.feature_schema_hash,
        generated_at=compiler.generated_at,
        feature_schema=tuple(VECTOR_FEATURES),
        profile_count=profile_count,
        vector_count=vector_count,
        groups={
            group: {
                feature: build_feature_statistics(values)
                for feature, values in sorted(features.items())
            }
            for group, features in sorted(grouped.items())
        },
    )


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def _write_json_atomically(payload: dict[str, Any], output_path: Path) -> Path:
    """Write a JSON document atomically with canonical formatting."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")

    temporary_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(output_path)

    return output_path


def save_calibration_vectors(
    artifact: CalibrationVectorArtifact,
    *,
    output_path: Path = DEFAULT_CALIBRATION_VECTORS_PATH,
) -> Path:
    """Write the consolidated calibration corpus atomically."""
    return _write_json_atomically(artifact.to_dict(), output_path)


def load_calibration_vectors(
    *,
    input_path: Path = DEFAULT_CALIBRATION_VECTORS_PATH,
) -> CalibrationVectorArtifact:
    """Load and validate the consolidated calibration corpus."""
    payload = json.loads(input_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Calibration artifact root must be an object.")

    return CalibrationVectorArtifact.from_dict(payload)


def save_calibration_statistics(
    artifact: CalibrationStatisticsArtifact,
    *,
    output_path: Path = DEFAULT_FEATURE_STATISTICS_PATH,
) -> Path:
    """Write precomputed calibration statistics atomically."""
    return _write_json_atomically(artifact.to_dict(), output_path)


def load_calibration_statistics(
    *,
    input_path: Path = DEFAULT_FEATURE_STATISTICS_PATH,
) -> CalibrationStatisticsArtifact:
    """Load and validate precomputed calibration statistics."""
    payload = json.loads(input_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Statistics artifact root must be an object.")

    return CalibrationStatisticsArtifact.from_dict(payload)


# ---------------------------------------------------------------------------
# Statistics-driven normalization
# ---------------------------------------------------------------------------


def normalize_feature_from_statistics(
    *,
    value: float,
    statistics: FeatureStatistics | None,
    mode: str,
) -> float:
    """Normalize one feature value against precomputed statistics.

    Mirrors ``atlas.ive.normalizer.normalize_feature_value`` exactly. When no
    statistics exist for the group the vector-based normalizer falls back to
    calibrating against the vector itself, which yields 0.5 for every
    population mode and a clamp for raw; that behaviour is reproduced here.
    """
    if mode not in {"percentile", "minmax", "zscore", "raw"}:
        raise ValueError(f"Unknown normalization mode: {mode}")

    if mode == "raw":
        return _clamp(value)

    if statistics is None or statistics.count == 0:
        return 0.5

    if mode == "percentile":
        ordered = statistics.sorted_values
        less = bisect_left(ordered, value)
        equal = bisect_right(ordered, value) - less

        return _clamp((less + 0.5 * equal) / statistics.count)

    if mode == "minmax":
        if statistics.maximum == statistics.minimum:
            return 0.5

        return _clamp(
            (value - statistics.minimum)
            / (statistics.maximum - statistics.minimum)
        )

    # zscore
    if statistics.count < 2 or statistics.stddev == 0:
        return 0.5

    z_score = (value - statistics.mean) / statistics.stddev

    return _clamp((z_score + 3.0) / 6.0)


def _clamp(value: float) -> float:
    """Clamp value to 0-1."""
    return max(0.0, min(1.0, float(value)))
