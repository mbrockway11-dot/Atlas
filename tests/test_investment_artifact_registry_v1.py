"""Tests for the canonical Atlas investment artifact registry."""

from __future__ import annotations

import pandas as pd
import pytest

from atlas.investment import artifacts
from atlas.investment.adaptive_research_prioritizer.loader import (
    SOURCE_PATHS as PRIORITIZER_PATHS,
)
from atlas.investment.experiment_registry.loader import (
    SOURCE_PATHS as EXPERIMENT_PATHS,
)
from atlas.investment.research_knowledge_graph.loader import (
    SOURCE_PATHS as GRAPH_PATHS,
)


def test_unknown_artifact_is_rejected():
    with pytest.raises(KeyError):
        artifacts.artifact_path("not_registered")


def test_registered_csv_loads(tmp_path, monkeypatch):
    path = tmp_path / "records.csv"
    path.write_text("value\n1\n", encoding="utf-8")

    monkeypatch.setitem(
        artifacts.ARTIFACTS,
        "test_csv",
        path,
    )

    frame = artifacts.load_csv("test_csv")

    assert frame["value"].tolist() == [1]


def test_empty_csv_returns_empty_frame(tmp_path, monkeypatch):
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")

    monkeypatch.setitem(
        artifacts.ARTIFACTS,
        "empty_csv",
        path,
    )

    assert artifacts.load_csv("empty_csv").empty


def test_json_loader_requires_object(tmp_path, monkeypatch):
    path = tmp_path / "payload.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")

    monkeypatch.setitem(
        artifacts.ARTIFACTS,
        "test_json",
        path,
    )

    assert artifacts.load_json("test_json") == {}


def test_loader_source_paths_use_canonical_registry():
    assert EXPERIMENT_PATHS[
        "validated_variants"
    ] == artifacts.artifact_path(
        "validated_variant_registry"
    )

    assert GRAPH_PATHS[
        "experiments"
    ] == artifacts.artifact_path(
        "experiment_registry"
    )

    assert PRIORITIZER_PATHS[
        "graph_nodes"
    ] == artifacts.artifact_path(
        "knowledge_graph_nodes"
    )


def test_missing_registered_csv_is_safe(tmp_path, monkeypatch):
    monkeypatch.setitem(
        artifacts.ARTIFACTS,
        "missing_csv",
        tmp_path / "missing.csv",
    )

    result = artifacts.load_csv("missing_csv")

    assert isinstance(result, pd.DataFrame)
    assert result.empty
