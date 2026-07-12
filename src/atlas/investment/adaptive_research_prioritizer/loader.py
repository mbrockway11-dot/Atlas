"""Adaptive Research Prioritizer source loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


SOURCE_PATHS = {
    "research_priorities": Path(
        "output/investment_meta_research/"
        "research_priorities.csv"
    ),
    "hypothesis_library": Path(
        "output/investment_meta_research/"
        "hypothesis_library.csv"
    ),
    "failure_modes": Path(
        "output/investment_meta_research/"
        "engine_failure_modes.csv"
    ),
    "family_gaps": Path(
        "output/investment_meta_research/"
        "engine_family_gaps.csv"
    ),
    "feature_interactions": Path(
        "output/investment_meta_research/"
        "feature_interactions.csv"
    ),
    "experiment_registry": Path(
        "output/investment_experiment_registry/"
        "experiment_registry.csv"
    ),
    "experiment_observations": Path(
        "output/investment_experiment_registry/"
        "experiment_observations.csv"
    ),
    "experiment_metrics": Path(
        "output/investment_experiment_registry/"
        "experiment_metrics.csv"
    ),
    "graph_nodes": Path(
        "output/investment_research_knowledge_graph/"
        "knowledge_graph_nodes.csv"
    ),
    "graph_edges": Path(
        "output/investment_research_knowledge_graph/"
        "knowledge_graph_edges.csv"
    ),
    "graph_metrics": Path(
        "output/investment_research_knowledge_graph/"
        "graph_metrics.csv"
    ),
    "validated_variants": Path(
        "output/investment_validated_variants/"
        "validated_variant_registry.csv"
    ),
    "variant_decisions": Path(
        "output/investment_variant_decisions/"
        "variant_decision_ledger.csv"
    ),
    "implementation_queue": Path(
        "output/investment_variant_decisions/"
        "implementation_queue.csv"
    ),
    "scheduler": Path(
        "output/investment_research_scheduler/"
        "research_schedule.csv"
    ),
    "regime_report": Path(
        "output/investment_regime_intelligence/"
        "regime_intelligence_report.json"
    ),
    "fusion_report": Path(
        "output/investment_macro_regime_fusion/"
        "macro_regime_fusion_report.json"
    ),
    "compiler_report": Path(
        "output/investment_atlas_compiler/"
        "atlas_compiler_report.json"
    ),
}


def load_prioritizer_sources() -> dict[str, Any]:
    """Load all available prioritizer evidence."""
    return {
        name: (
            safe_read_json(path)
            if path.suffix.lower() == ".json"
            else safe_read_csv(path)
        )
        for name, path in SOURCE_PATHS.items()
    }


def safe_read_csv(
    path: Path,
) -> pd.DataFrame:
    if (
        not path.exists()
        or not path.is_file()
        or path.stat().st_size == 0
    ):
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
        OSError,
    ):
        return pd.DataFrame()


def safe_read_json(
    path: Path,
) -> dict:
    if (
        not path.exists()
        or not path.is_file()
        or path.stat().st_size == 0
    ):
        return {}

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        OSError,
    ):
        return {}

    return (
        payload
        if isinstance(payload, dict)
        else {}
    )
