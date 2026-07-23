"""Runtime health for the Atlas compiled layer.

Answers one question: can the runtime be trusted right now? Silent drift is
the failure this exists to prevent -- artifacts compiled against an older
feature schema, statistics built from a corpus that has since changed, an
index that no longer matches what is on disk. Each of those still *works*,
returning plausible numbers, which is exactly why it needs surfacing.

Reads only manifest, index, and statistics headers by default, so it stays
cheap enough for a dashboard panel. Pass ``deep=True`` to stat every artifact
against its source, which is accurate but walks the whole corpus.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from atlas.compiled.calibration import (
    DEFAULT_CALIBRATION_VECTORS_PATH,
    DEFAULT_FEATURE_STATISTICS_PATH,
    load_calibration_statistics,
)
from atlas.compiled.compiler_identity import COMPILER_VERSION
from atlas.compiled.feature_schema import (
    current_feature_schema_hash,
    feature_schema_matches,
)
from atlas.compiled.identity_vector_artifact import (
    COMPILED_IDENTITY_VECTOR_SCHEMA,
)
from atlas.compiled.identity_vector_library_compiler import (
    list_compilable_profile_keys,
)
from atlas.compiled.identity_vector_store import (
    DEFAULT_COMPILED_VECTOR_DIR,
    artifact_path_for_profile,
    compiled_artifact_is_current,
    load_compiled_identity_vector,
)
from atlas.compiled.identity_vector_compiler import source_acf_path_for_profile
from atlas.compiled.index import DEFAULT_INDEX_PATH, load_compiled_index
from atlas.compiled.manifest import DEFAULT_MANIFEST_PATH
from atlas.library.profile_library import LIBRARY_DIR


# Health states, worst last -- overall status is the worst component state.
STATUS_OK = "ok"
STATUS_STALE = "stale"
STATUS_MISSING = "missing"
# An artifact whose source ACF is gone: it still loads, so it is not
# "missing", but it can no longer be rebuilt or verified against anything.
# Ranked above missing because a silent, unverifiable artifact is worse than
# an obviously absent one.
STATUS_SOURCE_MISSING = "source_missing"
STATUS_ERROR = "error"

_SEVERITY = {
    STATUS_OK: 0,
    STATUS_STALE: 1,
    STATUS_MISSING: 2,
    STATUS_SOURCE_MISSING: 3,
    STATUS_ERROR: 4,
}


@dataclass(frozen=True, slots=True)
class ComponentHealth:
    """Health of one compiled-layer component."""

    name: str
    status: str
    detail: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
            **self.data,
        }


@dataclass(frozen=True, slots=True)
class RuntimeHealth:
    """Overall compiled-runtime health."""

    status: str
    artifact_schema_version: str
    compiler_version: str
    feature_schema_hash: str
    components: tuple[ComponentHealth, ...]

    @property
    def healthy(self) -> bool:
        """Return whether every component is OK."""
        return self.status == STATUS_OK

    def problems(self) -> tuple[ComponentHealth, ...]:
        """Return components that are not OK, worst first."""
        return tuple(
            sorted(
                (c for c in self.components if c.status != STATUS_OK),
                key=lambda c: _SEVERITY[c.status],
                reverse=True,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "status": self.status,
            "healthy": self.healthy,
            "artifact_schema_version": self.artifact_schema_version,
            "compiler_version": self.compiler_version,
            "feature_schema_hash": self.feature_schema_hash,
            "components": [c.to_dict() for c in self.components],
        }


def _read_json(path: Path) -> dict[str, Any] | None:
    """Return a decoded JSON object, or None if unreadable."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    return payload if isinstance(payload, dict) else None


def orphaned_keys(artifact_dir: Path) -> list[str]:
    """Return compiled profiles whose source ACF no longer exists."""
    suffix = ".identity-vector.json"

    if not artifact_dir.is_dir():
        return []

    return sorted(
        entry.name[: -len(suffix)]
        for entry in artifact_dir.iterdir()
        if entry.is_file()
        and entry.name.endswith(suffix)
        and not source_acf_path_for_profile(
            entry.name[: -len(suffix)]
        ).is_file()
    )


def _manifest_health(manifest_path: Path) -> ComponentHealth:
    """Report on the compilation manifest."""
    if not manifest_path.is_file():
        return ComponentHealth(
            "manifest",
            STATUS_MISSING,
            "No compilation manifest. Run "
            "scripts/compile_identity_vectors_batch.py.",
        )

    payload = _read_json(manifest_path)

    if payload is None:
        return ComponentHealth(
            "manifest", STATUS_ERROR, f"Unreadable manifest: {manifest_path}"
        )

    recorded_schema = payload.get("feature_schema_hash")
    data = {
        "generated_at": payload.get("generated_at"),
        "compiler_version": payload.get("compiler_version"),
        "compiler_git_commit": payload.get("compiler_git_commit"),
        "compiler_git_dirty": payload.get("compiler_git_dirty"),
        "requested_count": payload.get("requested_count"),
        "successful_count": payload.get("successful_count"),
        "failed_count": payload.get("failed_count"),
        "total_vector_count": payload.get("total_vector_count"),
    }

    if payload.get("failed_count"):
        return ComponentHealth(
            "manifest",
            STATUS_STALE,
            f"{payload['failed_count']} profile(s) failed to compile.",
            data,
        )

    if not feature_schema_matches(recorded_schema):
        return ComponentHealth(
            "manifest",
            STATUS_STALE,
            "Manifest was built against a different feature schema.",
            data,
        )

    return ComponentHealth(
        "manifest", STATUS_OK, "Manifest matches the current schema.", data
    )


def _index_health(index_path: Path) -> ComponentHealth:
    """Report on the compiled corpus index."""
    if not index_path.is_file():
        return ComponentHealth(
            "index",
            STATUS_MISSING,
            "No compiled index. Run "
            "scripts/validate_compiled_vectors.py --write-index.",
        )

    try:
        index = load_compiled_index(input_path=index_path)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return ComponentHealth("index", STATUS_ERROR, f"Unreadable index: {exc}")

    data = {
        "profile_count": index.profile_count,
        "total_vector_count": index.total_vector_count,
        "total_artifact_bytes": index.total_artifact_bytes,
        "source_manifest_hash": index.source_manifest_hash,
        "entity_type_counts": index.entity_type_counts(),
    }

    if not feature_schema_matches(index.feature_schema_hash):
        return ComponentHealth(
            "index",
            STATUS_STALE,
            "Index was built against a different feature schema.",
            data,
        )

    return ComponentHealth(
        "index", STATUS_OK, "Index matches the current schema.", data
    )


def _statistics_health(
    statistics_path: Path,
    index_path: Path,
) -> ComponentHealth:
    """Report on normalization statistics and their corpus linkage."""
    if not statistics_path.is_file():
        return ComponentHealth(
            "statistics",
            STATUS_MISSING,
            "No normalization statistics. Run "
            "scripts/build_calibration_statistics.py.",
        )

    try:
        statistics = load_calibration_statistics(input_path=statistics_path)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return ComponentHealth(
            "statistics", STATUS_ERROR, f"Unreadable statistics: {exc}"
        )

    data = {
        "profile_count": statistics.profile_count,
        "vector_count": statistics.vector_count,
        "group_count": len(statistics.groups),
        "source_manifest_hash": statistics.source_manifest_hash,
        "consolidated_corpus_present": (
            DEFAULT_CALIBRATION_VECTORS_PATH.is_file()
        ),
    }

    if not feature_schema_matches(statistics.feature_schema_hash):
        return ComponentHealth(
            "statistics",
            STATUS_STALE,
            "Statistics were built against a different feature schema.",
            data,
        )

    # Statistics must describe the corpus the index currently reflects,
    # otherwise normalization silently calibrates against a stale population.
    # An unreadable index is the index component's problem to report, not
    # this one's -- skip the cross-check rather than fail here too.
    index = None

    if index_path.is_file():
        try:
            index = load_compiled_index(input_path=index_path)
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            index = None

    if (
        index is not None
        and index.source_manifest_hash != statistics.source_manifest_hash
    ):
        return ComponentHealth(
            "statistics",
            STATUS_STALE,
            "Statistics were built from a different corpus revision than "
            "the index. Rebuild with "
            "scripts/build_calibration_statistics.py.",
            data,
        )

    return ComponentHealth(
        "statistics", STATUS_OK, "Statistics match the current corpus.", data
    )


def _artifact_health(
    artifact_dir: Path,
    *,
    deep: bool,
    library_dir: Path,
) -> ComponentHealth:
    """Report on per-profile artifacts.

    Shallow mode compares counts only. Deep mode validates every artifact
    against its source, which is authoritative but walks the corpus.
    """
    profile_keys = list_compilable_profile_keys(library_dir=library_dir)
    suffix = ".identity-vector.json"

    present = (
        {
            entry.name[: -len(suffix)]
            for entry in artifact_dir.iterdir()
            if entry.is_file() and entry.name.endswith(suffix)
        }
        if artifact_dir.is_dir()
        else set()
    )

    missing = [key for key in profile_keys if key not in present]

    data: dict[str, Any] = {
        "source_profile_count": len(profile_keys),
        "artifact_count": len(present),
        "missing_count": len(missing),
        "missing_sample": missing[:10],
        "deep": deep,
    }

    if not present:
        return ComponentHealth(
            "artifacts",
            STATUS_MISSING,
            "No compiled artifacts. Run "
            "scripts/compile_identity_vectors_batch.py.",
            data,
        )

    if not deep:
        if missing:
            return ComponentHealth(
                "artifacts",
                STATUS_STALE,
                f"{len(missing)} profile(s) have no compiled artifact.",
                data,
            )

        return ComponentHealth(
            "artifacts",
            STATUS_OK,
            f"{len(present)} artifact(s) present for "
            f"{len(profile_keys)} source profile(s).",
            data,
        )

    stale: list[str] = []
    damaged: list[str] = []
    source_missing: list[str] = []

    # An artifact whose source ACF has disappeared is the dangerous case: the
    # compiled data still loads and still answers queries, so nothing looks
    # wrong, but the profile can no longer be rebuilt or verified. It is
    # reported separately from "stale" for exactly that reason.
    for profile_key in orphaned_keys(artifact_dir):
        source_missing.append(profile_key)

    for profile_key in profile_keys:
        if profile_key in missing:
            continue

        path = artifact_path_for_profile(profile_key, output_dir=artifact_dir)

        try:
            artifact = load_compiled_identity_vector(input_path=path)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            damaged.append(profile_key)
            continue

        if not compiled_artifact_is_current(
            artifact, source_acf_path_for_profile(profile_key)
        ):
            stale.append(profile_key)

    data.update(
        {
            "stale_count": len(stale),
            "damaged_count": len(damaged),
            "source_missing_count": len(source_missing),
            "stale_sample": stale[:10],
            "damaged_sample": damaged[:10],
            "source_missing_sample": source_missing[:10],
        }
    )

    if damaged:
        return ComponentHealth(
            "artifacts",
            STATUS_ERROR,
            f"{len(damaged)} artifact(s) are damaged or unreadable.",
            data,
        )

    if source_missing:
        return ComponentHealth(
            "artifacts",
            STATUS_SOURCE_MISSING,
            f"{len(source_missing)} artifact(s) have no source ACF. They "
            "still load but cannot be rebuilt or verified.",
            data,
        )

    if stale or missing:
        return ComponentHealth(
            "artifacts",
            STATUS_STALE,
            f"{len(stale)} stale, {len(missing)} missing.",
            data,
        )

    return ComponentHealth(
        "artifacts", STATUS_OK, f"All {len(present)} artifact(s) current.", data
    )


def build_runtime_health(
    *,
    artifact_dir: Path = DEFAULT_COMPILED_VECTOR_DIR,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    index_path: Path = DEFAULT_INDEX_PATH,
    statistics_path: Path = DEFAULT_FEATURE_STATISTICS_PATH,
    library_dir: Path = LIBRARY_DIR,
    deep: bool = False,
) -> RuntimeHealth:
    """Assess the compiled runtime and return a structured report."""
    components = (
        _manifest_health(manifest_path),
        _artifact_health(artifact_dir, deep=deep, library_dir=library_dir),
        _index_health(index_path),
        _statistics_health(statistics_path, index_path),
    )

    status = max(
        (component.status for component in components),
        key=lambda value: _SEVERITY[value],
    )

    return RuntimeHealth(
        status=status,
        artifact_schema_version=COMPILED_IDENTITY_VECTOR_SCHEMA,
        compiler_version=COMPILER_VERSION,
        feature_schema_hash=current_feature_schema_hash(),
        components=components,
    )
