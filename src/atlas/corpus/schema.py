"""Research corpus schema."""

from __future__ import annotations

from datetime import datetime, timezone


CORPUS_VERSION = "0.1.0"


def build_corpus_metadata(profile_count: int) -> dict:
    """Build corpus metadata."""
    return {
        "corpus_version": CORPUS_VERSION,
        "identity_vector_version": "0.3.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "profile_count": profile_count,
    }