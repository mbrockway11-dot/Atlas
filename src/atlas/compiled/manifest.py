"""Manifest support for Atlas compiled identity-vector artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from atlas.compiled.compiler_identity import build_compiler_identity
from atlas.compiled.identity_vector_artifact import (
    COMPILED_IDENTITY_VECTOR_SCHEMA,
)


COMPILED_MANIFEST_SCHEMA = "atlas.compiled.manifest.v1"
DEFAULT_MANIFEST_PATH = Path("output") / "compiled" / "manifest.json"


@dataclass(frozen=True, slots=True)
class CompilationManifest:
    """Summary and provenance for a compiler execution."""

    schema_version: str
    artifact_schema_version: str
    compiler_name: str
    compiler_version: str
    compiler_git_commit: str
    compiler_git_dirty: bool
    feature_schema_hash: str
    generated_at: str
    requested_count: int
    successful_count: int
    rebuilt_count: int
    reused_count: int
    failed_count: int
    total_vector_count: int
    total_source_bytes: int
    total_artifact_bytes: int
    elapsed_seconds: float
    storage_reduction_percent: float
    average_source_bytes: float
    average_artifact_bytes: float
    profiles_per_second: float
    failures: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert the manifest into JSON-safe values."""
        return asdict(self)


def build_compilation_manifest(
    *,
    requested_count: int,
    successful_count: int,
    rebuilt_count: int,
    reused_count: int,
    failed_count: int,
    total_vector_count: int,
    total_source_bytes: int,
    total_artifact_bytes: int,
    elapsed_seconds: float = 0.0,
    failures: tuple[dict[str, str], ...] = (),
) -> CompilationManifest:
    """Build a compilation manifest.

    Derived statistics (storage reduction, per-profile averages, and
    throughput) are computed here so every manifest reports them
    consistently. ``elapsed_seconds`` is supplied by the caller because
    only the batch runner can time the whole execution.
    """
    compiler = build_compiler_identity()

    if total_source_bytes > 0:
        storage_reduction_percent = max(
            0.0,
            (1.0 - (total_artifact_bytes / total_source_bytes)) * 100.0,
        )
    else:
        storage_reduction_percent = 0.0

    if successful_count > 0:
        average_source_bytes = total_source_bytes / successful_count
        average_artifact_bytes = total_artifact_bytes / successful_count
    else:
        average_source_bytes = 0.0
        average_artifact_bytes = 0.0

    if elapsed_seconds > 0.0:
        profiles_per_second = successful_count / elapsed_seconds
    else:
        profiles_per_second = 0.0

    return CompilationManifest(
        schema_version=COMPILED_MANIFEST_SCHEMA,
        artifact_schema_version=COMPILED_IDENTITY_VECTOR_SCHEMA,
        compiler_name=compiler.name,
        compiler_version=compiler.version,
        compiler_git_commit=compiler.git_commit,
        compiler_git_dirty=compiler.git_dirty,
        feature_schema_hash=compiler.feature_schema_hash,
        generated_at=datetime.now(UTC).isoformat(),
        requested_count=requested_count,
        successful_count=successful_count,
        rebuilt_count=rebuilt_count,
        reused_count=reused_count,
        failed_count=failed_count,
        total_vector_count=total_vector_count,
        total_source_bytes=total_source_bytes,
        total_artifact_bytes=total_artifact_bytes,
        elapsed_seconds=elapsed_seconds,
        storage_reduction_percent=storage_reduction_percent,
        average_source_bytes=average_source_bytes,
        average_artifact_bytes=average_artifact_bytes,
        profiles_per_second=profiles_per_second,
        failures=failures,
    )


def save_compilation_manifest(
    manifest: CompilationManifest,
    *,
    output_path: Path = DEFAULT_MANIFEST_PATH,
) -> Path:
    """Write the compiler manifest atomically."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(
        output_path.suffix + ".tmp"
    )

    temporary_path.write_text(
        json.dumps(
            manifest.to_dict(),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(output_path)

    return output_path
