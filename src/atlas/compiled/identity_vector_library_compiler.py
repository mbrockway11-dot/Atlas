"""Batch compiler over the entire Atlas profile library."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from atlas.compiled.identity_vector_artifact import (
    CompiledIdentityVectorArtifact,
)
from atlas.compiled.identity_vector_compiler import (
    compile_identity_vector_artifact,
)
from atlas.compiled.manifest import (
    DEFAULT_MANIFEST_PATH,
    CompilationManifest,
    build_compilation_manifest,
    save_compilation_manifest,
)
from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles


# The nominal vector count (3 ciphers x 7 planetary Kameas). Profiles that
# compile to a different count are surfaced as "irregular" rather than
# assumed broken -- the batch never hard-codes this expectation into a
# success/failure decision.
EXPECTED_VECTOR_COUNT = 21


CompileArtifactFunc = Callable[
    ...,
    tuple[CompiledIdentityVectorArtifact, Path, bool],
]
KeySource = Callable[[], Iterable[str]]


@dataclass(frozen=True, slots=True)
class ProfileCompilationOutcome:
    """Per-profile result from a batch compilation run."""

    profile_key: str
    success: bool
    rebuilt: bool
    vector_count: int
    source_bytes: int
    artifact_bytes: int
    output_path: str | None
    error_type: str | None
    error: str | None

    @property
    def irregular(self) -> bool:
        """Return whether a successful profile has an off-nominal count."""
        return self.success and self.vector_count != EXPECTED_VECTOR_COUNT

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe representation."""
        return {
            "profile_key": self.profile_key,
            "success": self.success,
            "rebuilt": self.rebuilt,
            "vector_count": self.vector_count,
            "source_bytes": self.source_bytes,
            "artifact_bytes": self.artifact_bytes,
            "output_path": self.output_path,
            "error_type": self.error_type,
            "error": self.error,
            "irregular": self.irregular,
        }


@dataclass(frozen=True, slots=True)
class LibraryCompilationResult:
    """Manifest plus per-profile outcomes for a batch compilation run."""

    manifest: CompilationManifest
    outcomes: tuple[ProfileCompilationOutcome, ...]

    def irregular_outcomes(self) -> tuple[ProfileCompilationOutcome, ...]:
        """Return successful outcomes whose vector count is off-nominal."""
        return tuple(o for o in self.outcomes if o.irregular)


def list_compilable_profile_keys(
    *,
    library_dir: Path = LIBRARY_DIR,
) -> tuple[str, ...]:
    """Return sorted profile keys that have a compilable ACF source."""
    if not library_dir.is_dir():
        return ()

    keys = [
        entry.name
        for entry in library_dir.iterdir()
        if entry.is_dir() and (entry / "profile.acf.json").is_file()
    ]

    return tuple(sorted(keys))


def storage_reduction_ratio(manifest: CompilationManifest) -> float:
    """Return the fraction of source bytes saved by compilation (0-1)."""
    if manifest.total_source_bytes <= 0:
        return 0.0

    ratio = 1.0 - (
        manifest.total_artifact_bytes / manifest.total_source_bytes
    )

    return max(0.0, ratio)


def compile_identity_vector_library(
    profile_keys: Iterable[str] | None = None,
    *,
    force: bool = False,
    limit: int | None = None,
    fail_fast: bool = False,
    write_manifest: bool = True,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    library_dir: Path | None = None,
    key_source: KeySource = list_saved_profiles,
    compile_func: CompileArtifactFunc = compile_identity_vector_artifact,
) -> LibraryCompilationResult:
    """Compile many saved profiles into vector artifacts.

    Key selection, in priority order:

    * ``profile_keys`` -- an explicit, de-duplicated set of keys.
    * ``library_dir`` -- scan a directory for profiles with an ACF source.
    * otherwise -- ``key_source`` (the saved-profile registry by default).

    ``limit`` caps the number of profiles processed. Failures are captured
    per profile so one broken ACF never aborts the run, unless ``fail_fast``
    is set, in which case the batch stops after the first failure. A
    compilation manifest is written unless ``write_manifest`` is disabled.
    """
    keys = _select_keys(
        profile_keys=profile_keys,
        library_dir=library_dir,
        key_source=key_source,
        limit=limit,
    )

    outcomes: list[ProfileCompilationOutcome] = []
    failures: list[dict[str, str]] = []

    successful_count = 0
    rebuilt_count = 0
    reused_count = 0
    failed_count = 0
    total_vector_count = 0
    total_source_bytes = 0
    total_artifact_bytes = 0

    started = perf_counter()

    for profile_key in keys:
        try:
            artifact, output_path, rebuilt = compile_func(
                profile_key,
                force=force,
            )
        except Exception as exc:  # noqa: BLE001 - one failure must not abort the batch
            failed_count += 1
            error_type = type(exc).__name__
            error = str(exc)

            failures.append(
                {
                    "profile_key": profile_key,
                    "error_type": error_type,
                    "error": error,
                }
            )
            outcomes.append(
                ProfileCompilationOutcome(
                    profile_key=profile_key,
                    success=False,
                    rebuilt=False,
                    vector_count=0,
                    source_bytes=0,
                    artifact_bytes=0,
                    output_path=None,
                    error_type=error_type,
                    error=error,
                )
            )

            if fail_fast:
                break

            continue

        artifact_bytes = (
            output_path.stat().st_size if output_path.is_file() else 0
        )

        successful_count += 1

        if rebuilt:
            rebuilt_count += 1
        else:
            reused_count += 1

        total_vector_count += artifact.vector_count
        total_source_bytes += artifact.source_acf_size_bytes
        total_artifact_bytes += artifact_bytes

        outcomes.append(
            ProfileCompilationOutcome(
                profile_key=profile_key,
                success=True,
                rebuilt=rebuilt,
                vector_count=artifact.vector_count,
                source_bytes=artifact.source_acf_size_bytes,
                artifact_bytes=artifact_bytes,
                output_path=str(output_path),
                error_type=None,
                error=None,
            )
        )

    elapsed_seconds = perf_counter() - started

    manifest = build_compilation_manifest(
        requested_count=len(keys),
        successful_count=successful_count,
        rebuilt_count=rebuilt_count,
        reused_count=reused_count,
        failed_count=failed_count,
        total_vector_count=total_vector_count,
        total_source_bytes=total_source_bytes,
        total_artifact_bytes=total_artifact_bytes,
        elapsed_seconds=elapsed_seconds,
        failures=tuple(failures),
    )

    if write_manifest:
        save_compilation_manifest(manifest, output_path=manifest_path)

    return LibraryCompilationResult(
        manifest=manifest,
        outcomes=tuple(outcomes),
    )


def _select_keys(
    *,
    profile_keys: Iterable[str] | None,
    library_dir: Path | None,
    key_source: KeySource,
    limit: int | None,
) -> tuple[str, ...]:
    """Resolve the ordered list of profile keys for a batch run."""
    if profile_keys is not None:
        keys = _dedupe_keys(profile_keys)
    elif library_dir is not None:
        keys = list_compilable_profile_keys(library_dir=library_dir)
    else:
        keys = _dedupe_keys(key_source())

    if limit is not None:
        if limit < 0:
            raise ValueError("limit cannot be negative")

        keys = keys[:limit]

    return keys


def _dedupe_keys(profile_keys: Iterable[str]) -> tuple[str, ...]:
    """Return cleaned, de-duplicated profile keys preserving order."""
    ordered: dict[str, None] = {}

    for raw_key in profile_keys:
        clean_key = raw_key.strip()

        if clean_key:
            ordered.setdefault(clean_key, None)

    return tuple(ordered)
