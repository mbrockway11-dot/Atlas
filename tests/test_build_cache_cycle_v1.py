"""Cycle-level tests for deterministic build-cache behavior."""

from __future__ import annotations

from atlas.investment.research_orchestrator import (
    build_cache,
)


def test_empty_cache_state_has_entries():
    state = build_cache.empty_cache_state()

    assert state["entries"] == {}
    assert (
        state["hash_algorithm"]
        == "sha256"
    )


def test_cache_invalidation_removes_entry(
    tmp_path,
):
    path = tmp_path / "cache.json"

    build_cache.write_build_cache(
        {
            "schema_version": "1.0.0",
            "hash_algorithm": "sha256",
            "entries": {
                "alpha": {
                    "identity_hash": "abc",
                }
            },
        },
        path=path,
    )

    assert (
        build_cache.invalidate_build_cache_entry(
            "alpha",
            path=path,
        )
    )

    state = build_cache.load_build_cache(
        path
    )

    assert "alpha" not in state[
        "entries"
    ]

    assert not (
        build_cache.invalidate_build_cache_entry(
            "alpha",
            path=path,
        )
    )
