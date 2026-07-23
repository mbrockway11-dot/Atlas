"""Hashing utilities for compiled Atlas artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path


DEFAULT_HASH_CHUNK_SIZE = 1024 * 1024


def sha256_file(
    path: Path,
    *,
    chunk_size: int = DEFAULT_HASH_CHUNK_SIZE,
) -> str:
    """Return the SHA-256 digest of a file."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    digest = hashlib.sha256()

    with path.open("rb") as source:
        while chunk := source.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()
