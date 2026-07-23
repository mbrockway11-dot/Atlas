"""Compiled-runtime entry points for identity comparison.

This module is the runtime face of the compiled layer. A comparison request
resolves to:

    load compiled artifact A
    load compiled artifact B
    load normalization statistics
    normalize
    compare

rather than reparsing the ACF corpus. ACFs stay authoritative as the
research representation; compiled artifacts are authoritative at runtime.

Artifacts are resolved through the ordinary compiler, so a missing, stale,
damaged, or old-schema artifact is rebuilt from its source ACF. When that
rebuild is impossible the caller gets a :class:`CompiledRuntimeError` --
the runtime never silently falls back to reparsing the whole corpus.
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from threading import Lock
from typing import Any

from atlas.compiled.calibration import (
    DEFAULT_FEATURE_STATISTICS_PATH,
    CalibrationStatisticsArtifact,
    load_calibration_statistics,
    normalize_feature_from_statistics,
)
from atlas.compiled.identity_vector_artifact import (
    CompiledIdentityVectorArtifact,
)
from atlas.compiled.identity_vector_compiler import (
    compile_identity_vector_artifact,
    source_acf_path_for_profile,
)
from atlas.ive.identity_vector import build_identity_vector_from_normalized
from atlas.ive.schema import (
    IVE_VERSION,
    VECTOR_FEATURES,
    IdentityVector,
    NormalizedPlanetVector,
    PlanetFeatureVector,
)


DEFAULT_ARTIFACT_CACHE_SIZE = 64

# "raw" needs no population context at all, so a raw comparison never pays
# for statistics loading.
MODES_REQUIRING_CALIBRATION = frozenset({"percentile", "minmax", "zscore"})


class CompiledRuntimeError(RuntimeError):
    """A compiled artifact could not be resolved for a profile."""


# ---------------------------------------------------------------------------
# Bounded in-process caches
# ---------------------------------------------------------------------------


class _ArtifactCache:
    """Bounded LRU cache of compiled artifacts, keyed by source identity.

    The cache key includes the source ACF's size and modification time. That
    is only a fast path for skipping revalidation -- content hashing still
    decides whether a persisted artifact is current. A spuriously changed
    mtime costs one extra validation, never a stale result.
    """

    def __init__(self, max_size: int = DEFAULT_ARTIFACT_CACHE_SIZE) -> None:
        self._entries: OrderedDict[
            str, tuple[tuple[int, int], CompiledIdentityVectorArtifact]
        ] = OrderedDict()
        self._max_size = max_size
        self._lock = Lock()

    def get(
        self,
        profile_key: str,
        stamp: tuple[int, int] | None,
    ) -> CompiledIdentityVectorArtifact | None:
        """Return a cached artifact when its source stamp still matches."""
        if stamp is None:
            return None

        with self._lock:
            entry = self._entries.get(profile_key)

            if entry is None or entry[0] != stamp:
                return None

            self._entries.move_to_end(profile_key)

            return entry[1]

    def put(
        self,
        profile_key: str,
        stamp: tuple[int, int] | None,
        artifact: CompiledIdentityVectorArtifact,
    ) -> None:
        """Store an artifact, evicting the least recently used entry."""
        if stamp is None:
            return

        with self._lock:
            self._entries[profile_key] = (stamp, artifact)
            self._entries.move_to_end(profile_key)

            while len(self._entries) > self._max_size:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        """Drop every cached artifact."""
        with self._lock:
            self._entries.clear()


_ARTIFACT_CACHE = _ArtifactCache()

_STATISTICS_LOCK = Lock()
_STATISTICS_CACHE: dict[
    Path, tuple[tuple[int, int], CalibrationStatisticsArtifact]
] = {}


def clear_runtime_caches() -> None:
    """Drop every in-process compiled-runtime cache."""
    _ARTIFACT_CACHE.clear()

    with _STATISTICS_LOCK:
        _STATISTICS_CACHE.clear()


def _file_stamp(path: Path) -> tuple[int, int] | None:
    """Return a cheap ``(size, mtime_ns)`` identity for a file."""
    try:
        stat = path.stat()
    except OSError:
        return None

    return (stat.st_size, stat.st_mtime_ns)


# ---------------------------------------------------------------------------
# Artifact and statistics resolution
# ---------------------------------------------------------------------------


def load_runtime_artifact(
    profile_key: str,
    *,
    use_cache: bool = True,
) -> CompiledIdentityVectorArtifact:
    """Return the current compiled artifact for a profile.

    Rebuilds from the source ACF when the persisted artifact is missing,
    stale, damaged, or written against an older schema. Raises
    :class:`CompiledRuntimeError` when no artifact can be produced.
    """
    stamp = _file_stamp(source_acf_path_for_profile(profile_key))

    if use_cache:
        cached = _ARTIFACT_CACHE.get(profile_key, stamp)

        if cached is not None:
            return cached

    try:
        artifact, _, _ = compile_identity_vector_artifact(profile_key)
    except Exception as exc:  # noqa: BLE001 - re-raised as a service error
        raise CompiledRuntimeError(
            f"Could not resolve compiled artifact for {profile_key!r}: {exc}"
        ) from exc

    if use_cache:
        _ARTIFACT_CACHE.put(profile_key, stamp, artifact)

    return artifact


def load_runtime_statistics(
    *,
    statistics_path: Path = DEFAULT_FEATURE_STATISTICS_PATH,
    use_cache: bool = True,
) -> CalibrationStatisticsArtifact:
    """Return precomputed normalization statistics.

    Raises :class:`CompiledRuntimeError` when the statistics artifact is
    absent or unreadable, so a population-normalized comparison fails
    loudly instead of quietly degrading to self-calibration.
    """
    stamp = _file_stamp(statistics_path)

    if use_cache and stamp is not None:
        with _STATISTICS_LOCK:
            entry = _STATISTICS_CACHE.get(statistics_path)

            if entry is not None and entry[0] == stamp:
                return entry[1]

    try:
        statistics = load_calibration_statistics(input_path=statistics_path)
    except Exception as exc:  # noqa: BLE001 - re-raised as a service error
        raise CompiledRuntimeError(
            "Could not load normalization statistics from "
            f"{statistics_path}: {exc}. Run "
            "scripts/build_calibration_statistics.py."
        ) from exc

    if use_cache and stamp is not None:
        with _STATISTICS_LOCK:
            _STATISTICS_CACHE[statistics_path] = (stamp, statistics)

    return statistics


# ---------------------------------------------------------------------------
# Statistics-driven normalization
# ---------------------------------------------------------------------------


def normalize_vectors_with_statistics(
    vectors: list[PlanetFeatureVector],
    statistics: CalibrationStatisticsArtifact | None,
    mode: str,
) -> list[NormalizedPlanetVector]:
    """Normalize raw vectors against precomputed population statistics.

    Numerically identical to ``normalize_planet_vectors`` given the same
    calibration population -- see ``tests/test_compiled_runtime_parity.py``.
    """
    normalized: list[NormalizedPlanetVector] = []

    for vector in vectors:
        group = (
            {
                feature: statistics.statistics_for(
                    cipher=vector.cipher,
                    planet=vector.planet,
                    feature=feature,
                )
                for feature in VECTOR_FEATURES
            }
            if statistics is not None
            else {feature: None for feature in VECTOR_FEATURES}
        )

        features = {
            feature: normalize_feature_from_statistics(
                value=vector.features[feature],
                statistics=group[feature],
                mode=mode,
            )
            for feature in VECTOR_FEATURES
        }

        present = [stats for stats in group.values() if stats is not None]
        calibration_size = present[0].count if present else 1

        normalized.append(
            NormalizedPlanetVector(
                version=IVE_VERSION,
                name=vector.name,
                cipher=vector.cipher,
                planet=vector.planet,
                kamea=vector.kamea,
                grid_size=vector.grid_size,
                features=features,
                raw_features=dict(vector.features),
                normalization_mode=mode,
                calibration_size=calibration_size,
            )
        )

    return normalized


# ---------------------------------------------------------------------------
# Identity vectors from the compiled runtime
# ---------------------------------------------------------------------------


def build_runtime_identity_vector(
    profile_key: str,
    *,
    normalization_mode: str = "raw",
    statistics: CalibrationStatisticsArtifact | None = None,
    use_cache: bool = True,
) -> tuple[IdentityVector, CompiledIdentityVectorArtifact]:
    """Build an IdentityVector for a profile from the compiled runtime.

    Returns the identity vector alongside the compiled artifact it came
    from, so callers can report provenance without a second load.
    """
    artifact = load_runtime_artifact(profile_key, use_cache=use_cache)

    if normalization_mode in MODES_REQUIRING_CALIBRATION and statistics is None:
        statistics = load_runtime_statistics(use_cache=use_cache)

    normalized = normalize_vectors_with_statistics(
        list(artifact.vectors),
        statistics if normalization_mode != "raw" else None,
        normalization_mode,
    )

    identity_vector = build_identity_vector_from_normalized(
        name=artifact.profile_name,
        normalized_vectors=normalized,
        normalization_mode=normalization_mode,
    )

    return identity_vector, artifact


def runtime_provenance(
    artifact: CompiledIdentityVectorArtifact,
) -> dict[str, Any]:
    """Return the provenance block describing one compiled artifact."""
    compiler = artifact.compiler

    return {
        "profile_key": artifact.profile_key,
        "schema_version": artifact.schema_version,
        "feature_schema_hash": artifact.feature_schema_hash,
        "content_hash": artifact.content_hash,
        "compiler_version": compiler.version,
        "compiler_git_commit": compiler.git_commit,
        "compiler_git_dirty": compiler.git_dirty,
        "compiled_at": compiler.generated_at,
        "source_acf_sha256": artifact.source_acf_sha256,
        "vector_count": artifact.vector_count,
    }
