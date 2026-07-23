"""Identity and provenance metadata for the Atlas compiled runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any

from atlas.compiled.feature_schema import current_feature_schema_hash


COMPILER_NAME = "Atlas Identity Vector Compiler"
COMPILER_VERSION = "1.2.0"


@dataclass(frozen=True, slots=True)
class CompilerIdentity:
    """Version, source-control, and environment identity for one run.

    Two commits with the same short hash can produce different artifacts if
    one had uncommitted changes, so ``git_dirty`` is recorded alongside the
    hash: a clean hash does not, on its own, describe what was compiled.
    """

    name: str
    version: str
    git_commit: str
    git_dirty: bool
    python_version: str
    platform: str
    atlas_version: str
    feature_schema_hash: str
    command: str
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CompilerIdentity":
        """Reconstruct from a decoded provenance block.

        Fields added after an artifact was written default sensibly: an
        unknown dirty state is conservatively ``True``, unknown strings are
        ``"unknown"``. This lets older artifacts load; freshness checks then
        decide whether to rebuild them.
        """
        return cls(
            name=str(payload["name"]),
            version=str(payload["version"]),
            git_commit=str(payload["git_commit"]),
            git_dirty=bool(payload.get("git_dirty", True)),
            python_version=str(payload.get("python_version", "unknown")),
            platform=str(payload.get("platform", "unknown")),
            atlas_version=str(payload.get("atlas_version", "unknown")),
            feature_schema_hash=str(payload.get("feature_schema_hash", "")),
            command=str(payload.get("command", "")),
            generated_at=str(payload.get("compiled_at")
                             or payload.get("generated_at", "")),
        )


def current_git_commit() -> str:
    """Return the current Git commit when available."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def current_git_dirty() -> bool:
    """Return whether the working tree has uncommitted changes.

    Unknown state (git missing, not a repo) is reported as ``True`` -- the
    conservative choice, since it never claims a build was clean when it may
    not have been.
    """
    try:
        output = subprocess.check_output(
            ["git", "status", "--porcelain"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return True

    return bool(output.strip())


def current_atlas_version() -> str:
    """Return the installed atlas package version, or 'unknown'."""
    try:
        from importlib.metadata import version

        return version("atlas")
    except Exception:  # noqa: BLE001 - provenance must never abort a compile
        return "unknown"


def current_command() -> str:
    """Return the invoking command, argv0 reduced to its basename."""
    if not sys.argv:
        return ""

    argv = [Path(sys.argv[0]).name, *sys.argv[1:]]

    return " ".join(argv)


def build_compiler_identity() -> CompilerIdentity:
    """Build provenance metadata for a compiler execution."""
    return CompilerIdentity(
        name=COMPILER_NAME,
        version=COMPILER_VERSION,
        git_commit=current_git_commit(),
        git_dirty=current_git_dirty(),
        python_version=platform.python_version(),
        platform=platform.platform(),
        atlas_version=current_atlas_version(),
        feature_schema_hash=current_feature_schema_hash(),
        command=current_command(),
        generated_at=datetime.now(UTC).isoformat(),
    )
