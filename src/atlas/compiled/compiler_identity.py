"""Identity and provenance metadata for the Atlas compiled runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import subprocess
from typing import Any


COMPILER_NAME = "Atlas Identity Vector Compiler"
COMPILER_VERSION = "1.1.0"


@dataclass(frozen=True, slots=True)
class CompilerIdentity:
    """Version and source-control identity for one compiler execution."""

    name: str
    version: str
    git_commit: str
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return asdict(self)


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


def build_compiler_identity() -> CompilerIdentity:
    """Build provenance metadata for a compiler execution."""
    return CompilerIdentity(
        name=COMPILER_NAME,
        version=COMPILER_VERSION,
        git_commit=current_git_commit(),
        generated_at=datetime.now(UTC).isoformat(),
    )
