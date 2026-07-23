"""Compiled corpus index for the Atlas runtime.

``output/compiled/index.json`` maps every profile key to the metadata a
caller needs before deciding to open an artifact: where it lives, what it
is, how many vectors it holds, and which source revision produced it.

The point is to make routine questions -- profile lookup, entity-type
filtering, corpus browsing, artifact validation -- answerable without
scanning a directory of thousands of files or parsing any of them.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable

from atlas.compiled.calibration import source_manifest_hash
from atlas.compiled.compiler_identity import build_compiler_identity
from atlas.compiled.identity_vector_artifact import (
    COMPILED_IDENTITY_VECTOR_SCHEMA,
)
from atlas.compiled.identity_vector_store import (
    DEFAULT_COMPILED_VECTOR_DIR,
    load_compiled_identity_vector,
)


COMPILED_INDEX_SCHEMA = "atlas.compiled.index.v1"
DEFAULT_INDEX_PATH = Path("output") / "compiled" / "index.json"

ARTIFACT_SUFFIX = ".identity-vector.json"


@dataclass(frozen=True, slots=True)
class CompiledIndexEntry:
    """Metadata for one compiled artifact."""

    profile_key: str
    path: str
    profile_name: str
    entity_type: str
    vector_count: int
    source_hash: str
    artifact_bytes: int

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON-safe entry body, without the key itself."""
        return {
            "path": self.path,
            "profile_name": self.profile_name,
            "entity_type": self.entity_type,
            "vector_count": self.vector_count,
            "source_hash": self.source_hash,
            "artifact_bytes": self.artifact_bytes,
        }

    @classmethod
    def from_dict(
        cls,
        profile_key: str,
        payload: dict[str, Any],
    ) -> "CompiledIndexEntry":
        """Rebuild one entry from decoded JSON."""
        return cls(
            profile_key=profile_key,
            path=str(payload["path"]),
            profile_name=str(payload["profile_name"]),
            entity_type=str(payload["entity_type"]),
            vector_count=int(payload["vector_count"]),
            source_hash=str(payload["source_hash"]),
            artifact_bytes=int(payload["artifact_bytes"]),
        )


@dataclass(frozen=True, slots=True)
class CompiledIndex:
    """The compiled corpus index."""

    schema_version: str
    artifact_schema_version: str
    source_manifest_hash: str
    compiler_name: str
    compiler_version: str
    compiler_git_commit: str
    generated_at: str
    profile_count: int
    total_vector_count: int
    total_artifact_bytes: int
    entries: dict[str, CompiledIndexEntry]

    def keys_by_entity_type(self, entity_type: str) -> tuple[str, ...]:
        """Return sorted profile keys matching one entity type."""
        return tuple(
            sorted(
                key
                for key, entry in self.entries.items()
                if entry.entity_type == entity_type
            )
        )

    def entity_type_counts(self) -> dict[str, int]:
        """Return profile counts per entity type."""
        counts: dict[str, int] = {}

        for entry in self.entries.values():
            counts[entry.entity_type] = counts.get(entry.entity_type, 0) + 1

        return dict(sorted(counts.items()))

    def irregular_keys(self, expected_vector_count: int) -> tuple[str, ...]:
        """Return keys whose vector count is off-nominal."""
        return tuple(
            sorted(
                key
                for key, entry in self.entries.items()
                if entry.vector_count != expected_vector_count
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert into JSON-safe primitive values."""
        return {
            "schema_version": self.schema_version,
            "artifact_schema_version": self.artifact_schema_version,
            "source_manifest_hash": self.source_manifest_hash,
            "compiler": {
                "name": self.compiler_name,
                "version": self.compiler_version,
                "git_commit": self.compiler_git_commit,
                "generated_at": self.generated_at,
            },
            "profile_count": self.profile_count,
            "total_vector_count": self.total_vector_count,
            "total_artifact_bytes": self.total_artifact_bytes,
            "profiles": {
                key: entry.to_dict()
                for key, entry in sorted(self.entries.items())
            },
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CompiledIndex":
        """Reconstruct and validate from decoded JSON."""
        schema_version = str(payload["schema_version"])

        if schema_version != COMPILED_INDEX_SCHEMA:
            raise ValueError(
                f"Unsupported compiled index schema: {schema_version!r}"
            )

        compiler = payload["compiler"]

        return cls(
            schema_version=schema_version,
            artifact_schema_version=str(payload["artifact_schema_version"]),
            source_manifest_hash=str(payload["source_manifest_hash"]),
            compiler_name=str(compiler["name"]),
            compiler_version=str(compiler["version"]),
            compiler_git_commit=str(compiler["git_commit"]),
            generated_at=str(compiler["generated_at"]),
            profile_count=int(payload["profile_count"]),
            total_vector_count=int(payload["total_vector_count"]),
            total_artifact_bytes=int(payload["total_artifact_bytes"]),
            entries={
                str(key): CompiledIndexEntry.from_dict(str(key), entry)
                for key, entry in payload["profiles"].items()
            },
        )


def build_compiled_index(
    *,
    artifact_dir: Path = DEFAULT_COMPILED_VECTOR_DIR,
    profile_keys: Iterable[str] | None = None,
    relative_to: Path | None = None,
) -> CompiledIndex:
    """Scan compiled artifacts and build the corpus index.

    Recorded paths are relative to ``relative_to`` (the artifact
    directory's parent by default), so the index stays portable across
    checkouts rather than embedding absolute paths.
    """
    if not artifact_dir.is_dir():
        raise FileNotFoundError(
            f"Compiled artifact directory does not exist: {artifact_dir}"
        )

    root = relative_to if relative_to is not None else artifact_dir.parent

    if profile_keys is None:
        paths = sorted(
            entry
            for entry in artifact_dir.iterdir()
            if entry.is_file() and entry.name.endswith(ARTIFACT_SUFFIX)
        )
    else:
        paths = [
            artifact_dir / f"{key.strip()}{ARTIFACT_SUFFIX}"
            for key in profile_keys
            if key and key.strip()
        ]

    entries: dict[str, CompiledIndexEntry] = {}
    sources: list[tuple[str, str]] = []

    total_vector_count = 0
    total_artifact_bytes = 0

    for path in paths:
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

        artifact_bytes = path.stat().st_size

        try:
            relative_path = path.relative_to(root).as_posix()
        except ValueError:
            relative_path = path.as_posix()

        entries[artifact.profile_key] = CompiledIndexEntry(
            profile_key=artifact.profile_key,
            path=relative_path,
            profile_name=artifact.profile_name,
            entity_type=artifact.entity_type,
            vector_count=artifact.vector_count,
            source_hash=artifact.source_acf_sha256,
            artifact_bytes=artifact_bytes,
        )

        sources.append((artifact.profile_key, artifact.source_acf_sha256))
        total_vector_count += artifact.vector_count
        total_artifact_bytes += artifact_bytes

    compiler = build_compiler_identity()

    return CompiledIndex(
        schema_version=COMPILED_INDEX_SCHEMA,
        artifact_schema_version=COMPILED_IDENTITY_VECTOR_SCHEMA,
        source_manifest_hash=source_manifest_hash(sources),
        compiler_name=compiler.name,
        compiler_version=compiler.version,
        compiler_git_commit=compiler.git_commit,
        generated_at=compiler.generated_at,
        profile_count=len(entries),
        total_vector_count=total_vector_count,
        total_artifact_bytes=total_artifact_bytes,
        entries=entries,
    )


def save_compiled_index(
    index: CompiledIndex,
    *,
    output_path: Path = DEFAULT_INDEX_PATH,
) -> Path:
    """Write the compiled corpus index atomically."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")

    temporary_path.write_text(
        json.dumps(
            index.to_dict(),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(output_path)

    return output_path


def load_compiled_index(
    *,
    input_path: Path = DEFAULT_INDEX_PATH,
) -> CompiledIndex:
    """Load and validate the compiled corpus index."""
    payload = json.loads(input_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Compiled index root must be an object.")

    return CompiledIndex.from_dict(payload)
