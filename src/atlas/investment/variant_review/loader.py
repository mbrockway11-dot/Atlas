"""Variant Review Board v1 loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.validated_variants.builder import (
    build_variant_id,
)


VARIANT_REGISTRY = Path(
    "output/investment_validated_variants/"
    "validated_variant_registry.csv"
)

VARIANT_CONFLICTS = Path(
    "output/investment_validated_variants/"
    "validated_variant_conflicts.csv"
)

VALIDATION_FOLDS = Path(
    "output/investment_hypothesis_validation/"
    "hypothesis_validation_folds.csv"
)

RESEARCH_PRIORITIES = Path(
    "output/investment_meta_research/"
    "research_priorities.csv"
)

LEARNING_MEMORY = Path(
    "output/investment_learning/"
    "strategy_memory_summary.csv"
)

GOVERNANCE_SNAPSHOTS = Path(
    "output/investment_governance_snapshots/"
    "engine_governance_snapshots.csv"
)

ENGINE_PERFORMANCE = Path(
    "output/investment_alpha_engines/"
    "historical_alpha_engine_performance.csv"
)

ACCUMULATED_VARIANT_EVIDENCE = Path(
    "output/investment_research_evidence_accumulator/"
    "accumulated_variant_evidence.csv"
)

EXPERIMENT_VARIANTS = Path(
    "output/investment_research_experiment_designer/"
    "experiment_variants.csv"
)

EXPERIMENT_DESIGNS = Path(
    "output/investment_research_experiment_designer/"
    "research_experiment_designs.csv"
)


def load_variant_review_inputs() -> dict[str, Any]:
    """Load canonical variant-review evidence."""
    accumulated = safe_read_csv(
        ACCUMULATED_VARIANT_EVIDENCE
    )

    experiment_variants = safe_read_csv(
        EXPERIMENT_VARIANTS
    )

    experiment_designs = safe_read_csv(
        EXPERIMENT_DESIGNS
    )

    longitudinal = enrich_longitudinal_evidence(
        accumulated_evidence=accumulated,
        experiment_variants=experiment_variants,
        experiment_designs=experiment_designs,
    )

    return {
        "registry": safe_read_csv(
            VARIANT_REGISTRY
        ),
        "conflicts": safe_read_csv(
            VARIANT_CONFLICTS
        ),
        "validation_folds": safe_read_csv(
            VALIDATION_FOLDS
        ),
        "research_priorities": safe_read_csv(
            RESEARCH_PRIORITIES
        ),
        "learning_memory": safe_read_csv(
            LEARNING_MEMORY
        ),
        "governance_snapshots": safe_read_csv(
            GOVERNANCE_SNAPSHOTS
        ),
        "engine_performance": safe_read_csv(
            ENGINE_PERFORMANCE
        ),
        "accumulated_variant_evidence": (
            longitudinal
        ),
    }


def enrich_longitudinal_evidence(
    *,
    accumulated_evidence: pd.DataFrame,
    experiment_variants: pd.DataFrame,
    experiment_designs: pd.DataFrame,
) -> pd.DataFrame:
    """Attach canonical registry IDs using stable research lineage."""
    if (
        accumulated_evidence is None
        or accumulated_evidence.empty
        or experiment_variants is None
        or experiment_variants.empty
        or experiment_designs is None
        or experiment_designs.empty
    ):
        return pd.DataFrame()

    required_evidence = {
        "research_program_id",
        "source_candidate_id",
    }

    required_variants = {
        "experiment_id",
        "source_candidate_id",
        "feature_name",
        "condition_value",
    }

    required_designs = {
        "experiment_id",
        "research_program_id",
        "parent_engine_id",
    }

    if not required_evidence.issubset(
        accumulated_evidence.columns
    ):
        return pd.DataFrame()

    if not required_variants.issubset(
        experiment_variants.columns
    ):
        return pd.DataFrame()

    if not required_designs.issubset(
        experiment_designs.columns
    ):
        return pd.DataFrame()

    design_lineage = (
        experiment_designs[
            [
                "experiment_id",
                "research_program_id",
                "parent_engine_id",
            ]
        ]
        .dropna(
            subset=[
                "experiment_id",
                "research_program_id",
                "parent_engine_id",
            ]
        )
        .drop_duplicates(
            subset=[
                "experiment_id",
            ],
            keep="last",
        )
    )

    current_lineage = (
        experiment_variants[
            [
                "experiment_id",
                "experiment_variant_id",
                "source_candidate_id",
                "feature_name",
                "condition_value",
            ]
        ]
        .dropna(
            subset=[
                "experiment_id",
                "source_candidate_id",
                "feature_name",
                "condition_value",
            ]
        )
        .merge(
            design_lineage,
            on="experiment_id",
            how="inner",
        )
        .drop_duplicates(
            subset=[
                "research_program_id",
                "source_candidate_id",
            ],
            keep="last",
        )
    )

    enriched = accumulated_evidence.merge(
        current_lineage,
        on=[
            "research_program_id",
            "source_candidate_id",
        ],
        how="inner",
        suffixes=(
            "",
            "_current",
        ),
    )

    if enriched.empty:
        return pd.DataFrame()

    enriched[
        "variant_id"
    ] = enriched.apply(
        lambda row: build_variant_id(
            parent_engine_id=str(
                row["parent_engine_id"]
            ),
            hypothesis_type=(
                "FAILURE_MODE_GATE"
            ),
            feature=str(
                row["feature_name"]
            ),
            state=str(
                row["condition_value"]
            ).upper(),
        ),
        axis=1,
    )

    return enriched.reset_index(
        drop=True
    )

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



