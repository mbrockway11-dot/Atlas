"""Tests for Atlas compiler framework."""

from __future__ import annotations

from dataclasses import replace

import pytest

from atlas.core.canonical_structural_signature import CanonicalStructuralSignature
from atlas.core.compiler_framework import (
    CompilerContext,
    CompilerEngine,
    PassMetadata,
    PassRegistry,
    order_passes_by_dependency,
)


class DummyPass:
    def __init__(self, name: str, dependencies: tuple[str, ...] = ()):
        self.metadata = PassMetadata(name=name, dependencies=dependencies)

    def run(self, css, context):
        metadata = dict(css.metadata)
        metadata.setdefault("ran", []).append(self.metadata.name)
        return replace(css, metadata=metadata)


class FailingPass:
    metadata = PassMetadata(name="failing")

    def run(self, css, context):
        raise RuntimeError("intentional failure")


def make_context() -> CompilerContext:
    return CompilerContext(
        profile_key="test_profile",
        profile_payload={},
    )


def test_pass_registry_rejects_duplicate_names():
    registry = PassRegistry()
    registry.register(DummyPass("identity"))

    with pytest.raises(ValueError, match="Duplicate compiler pass"):
        registry.register(DummyPass("identity"))


def test_dependency_ordering_reorders_passes():
    identity = DummyPass("identity")
    cipher = DummyPass("cipher", dependencies=("identity",))
    kamea = DummyPass("kamea", dependencies=("cipher",))

    ordered = order_passes_by_dependency([kamea, cipher, identity])

    assert [compiler_pass.metadata.name for compiler_pass in ordered] == [
        "identity",
        "cipher",
        "kamea",
    ]


def test_dependency_ordering_detects_missing_dependency():
    kamea = DummyPass("kamea", dependencies=("cipher",))

    with pytest.raises(ValueError, match="Missing compiler pass dependency"):
        order_passes_by_dependency([kamea])


def test_dependency_ordering_detects_cycle():
    first = DummyPass("first", dependencies=("second",))
    second = DummyPass("second", dependencies=("first",))

    with pytest.raises(ValueError, match="dependency cycle"):
        order_passes_by_dependency([first, second])


def test_engine_runs_passes_in_dependency_order():
    engine = CompilerEngine()
    engine.register(DummyPass("kamea", dependencies=("cipher",)))
    engine.register(DummyPass("identity"))
    engine.register(DummyPass("cipher", dependencies=("identity",)))

    css, results = engine.run(CanonicalStructuralSignature(), make_context())

    assert css.metadata["ran"] == ["identity", "cipher", "kamea"]
    assert [result.name for result in results] == ["identity", "cipher", "kamea"]
    assert all(result.success for result in results)
    assert all(result.elapsed_ms is not None for result in results)


def test_engine_reports_failed_pass_without_crashing():
    engine = CompilerEngine()
    engine.register(FailingPass())

    css, results = engine.run(CanonicalStructuralSignature(), make_context())

    assert css.metadata == {}
    assert len(results) == 1
    assert results[0].name == "failing"
    assert results[0].success is False
    assert results[0].errors == ("intentional failure",)
