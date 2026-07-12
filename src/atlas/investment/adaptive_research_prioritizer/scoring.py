"""Adaptive Research Prioritizer scoring engine."""

from __future__ import annotations

from typing import Any

import pandas as pd

from atlas.investment.adaptive_research_prioritizer.config import (
    PRIORITY_THRESHOLDS,
    RECOMMENDATION_THRESHOLDS,
    SCORE_WEIGHTS,
)
from atlas.investment.adaptive_research_prioritizer.utils import (
    boolean,
    clamp,
    integer,
    jaccard_similarity,
    number,
    text,
)


SCORE_COLUMNS = [
    "candidate_id",
    "natural_key",
    "candidate_type",
    "title",
    "parent_engine_id",
    "engine_family",
    "source_priority_score",
    "failure_recurrence_score",
    "coverage_gap_score",
    "graph_importance_score",
    "validation_potential_score",
    "regime_relevance_score",
    "novelty_score",
    "implementation_readiness_score",
    "evidence_quality_score",
    "duplication_penalty",
    "final_priority_score",
    "priority_band",
    "recommendation",
    "rank_eligible",
    "execution_instruction",
]


def score_research_candidates(
    candidates: pd.DataFrame,
    sources: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    """Score every canonical research candidate."""
    if candidates is None or candidates.empty:
        empty = pd.DataFrame(
            columns=SCORE_COLUMNS
        )

        return {
            "scores": empty,
            "components": pd.DataFrame(),
            "duplication_flags": (
                pd.DataFrame()
            ),
            "coverage_gaps": (
                build_coverage_gap_table(
                    sources
                )
            ),
        }

    graph_metrics = graph_metric_map(
        sources.get(
            "graph_metrics",
            pd.DataFrame(),
        ),
        sources.get(
            "graph_nodes",
            pd.DataFrame(),
        ),
    )

    failure_map = failure_recurrence_map(
        sources.get(
            "failure_modes",
            pd.DataFrame(),
        )
    )

    coverage_map = coverage_gap_map(
        sources.get(
            "family_gaps",
            pd.DataFrame(),
        )
    )

    existing_experiments = sources.get(
        "experiment_registry",
        pd.DataFrame(),
    )

    validated_variants = sources.get(
        "validated_variants",
        pd.DataFrame(),
    )

    variant_decisions = sources.get(
        "variant_decisions",
        pd.DataFrame(),
    )

    implementation_queue = sources.get(
        "implementation_queue",
        pd.DataFrame(),
    )

    regime_context = extract_regime_context(
        sources
    )

    score_rows = []
    component_rows = []
    duplication_rows = []

    for _, candidate in candidates.iterrows():
        data = candidate.to_dict()

        source_priority = clamp(
            data.get(
                "source_priority",
                0.50,
            )
        )

        failure_recurrence = (
            score_failure_recurrence(
                data,
                failure_map,
            )
        )

        coverage_gap = score_coverage_gap(
            data,
            coverage_map,
        )

        graph_importance = (
            score_graph_importance(
                data,
                graph_metrics,
            )
        )

        validation_potential = (
            score_validation_potential(
                data,
                validated_variants,
                existing_experiments,
            )
        )

        regime_relevance = (
            score_regime_relevance(
                data,
                regime_context,
            )
        )

        duplication = (
            score_duplication(
                data,
                existing_experiments,
            )
        )

        novelty = clamp(
            1.0 - duplication[
                "similarity"
            ]
        )

        implementation_readiness = (
            score_implementation_readiness(
                data,
                variant_decisions,
                implementation_queue,
            )
        )

        evidence_quality = (
            score_evidence_quality(
                data
            )
        )

        duplication_penalty = clamp(
            duplication["similarity"]
            * 0.20
        )

        weighted = {
            "source_priority": (
                source_priority
                * SCORE_WEIGHTS[
                    "source_priority"
                ]
            ),
            "failure_recurrence": (
                failure_recurrence
                * SCORE_WEIGHTS[
                    "failure_recurrence"
                ]
            ),
            "coverage_gap": (
                coverage_gap
                * SCORE_WEIGHTS[
                    "coverage_gap"
                ]
            ),
            "graph_importance": (
                graph_importance
                * SCORE_WEIGHTS[
                    "graph_importance"
                ]
            ),
            "validation_potential": (
                validation_potential
                * SCORE_WEIGHTS[
                    "validation_potential"
                ]
            ),
            "regime_relevance": (
                regime_relevance
                * SCORE_WEIGHTS[
                    "regime_relevance"
                ]
            ),
            "novelty": (
                novelty
                * SCORE_WEIGHTS[
                    "novelty"
                ]
            ),
            "implementation_readiness": (
                implementation_readiness
                * SCORE_WEIGHTS[
                    "implementation_readiness"
                ]
            ),
            "evidence_quality": (
                evidence_quality
                * SCORE_WEIGHTS[
                    "evidence_quality"
                ]
            ),
        }

        final_score = clamp(
            sum(
                weighted.values()
            )
            - duplication_penalty
        )

        priority_band = classify_band(
            final_score,
            PRIORITY_THRESHOLDS,
        )

        recommendation = classify_band(
            final_score,
            RECOMMENDATION_THRESHOLDS,
        )

        rank_eligible = not bool(
            duplication["exact_match"]
        )

        score_rows.append({
            "candidate_id": data[
                "candidate_id"
            ],
            "natural_key": data[
                "natural_key"
            ],
            "candidate_type": data[
                "candidate_type"
            ],
            "title": data["title"],
            "parent_engine_id": data[
                "parent_engine_id"
            ],
            "engine_family": data[
                "engine_family"
            ],
            "source_priority_score": round(
                source_priority,
                8,
            ),
            "failure_recurrence_score": round(
                failure_recurrence,
                8,
            ),
            "coverage_gap_score": round(
                coverage_gap,
                8,
            ),
            "graph_importance_score": round(
                graph_importance,
                8,
            ),
            "validation_potential_score": round(
                validation_potential,
                8,
            ),
            "regime_relevance_score": round(
                regime_relevance,
                8,
            ),
            "novelty_score": round(
                novelty,
                8,
            ),
            "implementation_readiness_score": round(
                implementation_readiness,
                8,
            ),
            "evidence_quality_score": round(
                evidence_quality,
                8,
            ),
            "duplication_penalty": round(
                duplication_penalty,
                8,
            ),
            "final_priority_score": round(
                final_score,
                8,
            ),
            "priority_band": (
                priority_band
            ),
            "recommendation": (
                recommendation
            ),
            "rank_eligible": bool(
                rank_eligible
            ),
            "execution_instruction": False,
        })

        for component, weighted_value in (
            weighted.items()
        ):
            component_rows.append({
                "candidate_id": data[
                    "candidate_id"
                ],
                "component": component,
                "raw_score": round(
                    {
                        "source_priority": source_priority,
                        "failure_recurrence": failure_recurrence,
                        "coverage_gap": coverage_gap,
                        "graph_importance": graph_importance,
                        "validation_potential": validation_potential,
                        "regime_relevance": regime_relevance,
                        "novelty": novelty,
                        "implementation_readiness": implementation_readiness,
                        "evidence_quality": evidence_quality,
                    }[component],
                    8,
                ),
                "weight": SCORE_WEIGHTS[
                    component
                ],
                "weighted_score": round(
                    weighted_value,
                    8,
                ),
                "execution_instruction": False,
            })

        duplication_rows.append({
            "candidate_id": data[
                "candidate_id"
            ],
            "candidate_title": data[
                "title"
            ],
            "matched_experiment_id": (
                duplication[
                    "experiment_id"
                ]
            ),
            "matched_title": (
                duplication[
                    "matched_title"
                ]
            ),
            "similarity": round(
                duplication[
                    "similarity"
                ],
                8,
            ),
            "exact_match": bool(
                duplication[
                    "exact_match"
                ]
            ),
            "duplicate_status": (
                duplication[
                    "status"
                ]
            ),
            "execution_instruction": False,
        })

    scores = pd.DataFrame(
        score_rows
    )

    scores = (
        scores.sort_values(
            [
                "rank_eligible",
                "final_priority_score",
                "source_priority_score",
                "candidate_id",
            ],
            ascending=[
                False,
                False,
                False,
                True,
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )

    return {
        "scores": scores,
        "components": pd.DataFrame(
            component_rows
        ),
        "duplication_flags": pd.DataFrame(
            duplication_rows
        ),
        "coverage_gaps": (
            build_coverage_gap_table(
                sources
            )
        ),
    }


def score_failure_recurrence(
    candidate: dict,
    failure_map: dict,
) -> float:
    keys = [
        text(
            candidate.get(
                "failure_mode"
            )
        ),
        text(
            candidate.get(
                "parent_engine_id"
            )
        ),
    ]

    values = [
        failure_map.get(
            key,
            0.0,
        )
        for key in keys
        if key
    ]

    return max(
        values,
        default=0.15,
    )


def score_coverage_gap(
    candidate: dict,
    coverage_map: dict,
) -> float:
    family = text(
        candidate.get(
            "engine_family"
        )
    )

    if (
        candidate.get(
            "candidate_type"
        )
        == "ENGINE_FAMILY_GAP"
    ):
        return max(
            coverage_map.get(
                family,
                0.80,
            ),
            0.80,
        )

    return coverage_map.get(
        family,
        0.20,
    )


def score_graph_importance(
    candidate: dict,
    graph_metrics: dict,
) -> float:
    keys = [
        text(
            candidate.get(
                "hypothesis_id"
            )
        ),
        text(
            candidate.get(
                "parent_engine_id"
            )
        ),
    ]

    return max(
        [
            graph_metrics.get(
                key,
                0.0,
            )
            for key in keys
            if key
        ],
        default=0.15,
    )


def score_validation_potential(
    candidate: dict,
    validated_variants: pd.DataFrame,
    experiments: pd.DataFrame,
) -> float:
    candidate_type = text(
        candidate.get(
            "candidate_type"
        )
    )

    base = {
        "FAILURE_MODE_GATE": 0.80,
        "HYPOTHESIS": 0.70,
        "RESEARCH_PRIORITY": 0.65,
        "ENGINE_FAMILY_GAP": 0.55,
    }.get(
        candidate_type,
        0.50,
    )

    engine_id = text(
        candidate.get(
            "parent_engine_id"
        )
    )

    if (
        validated_variants is not None
        and not validated_variants.empty
        and engine_id
    ):
        engine_columns = [
            column
            for column in (
                "parent_engine_id",
                "engine_id",
            )
            if column
            in validated_variants.columns
        ]

        if engine_columns:
            matching = validated_variants[
                validated_variants[
                    engine_columns[0]
                ].astype(str).eq(
                    engine_id
                )
            ]

            if not matching.empty:
                base += 0.10

    return clamp(base)


def score_regime_relevance(
    candidate: dict,
    context: dict,
) -> float:
    searchable = " ".join([
        text(
            candidate.get(
                "title"
            )
        ),
        text(
            candidate.get(
                "description"
            )
        ),
        text(
            candidate.get(
                "failure_mode"
            )
        ),
        text(
            candidate.get(
                "proposed_gate"
            )
        ),
    ]).lower()

    regime_terms = {
        text(
            context.get(
                "regime"
            )
        ).lower(),
        text(
            context.get(
                "primary_regime"
            )
        ).lower(),
        text(
            context.get(
                "secondary_regime"
            )
        ).lower(),
    }

    regime_terms = {
        term
        for term in regime_terms
        if term
    }

    if any(
        term.replace(
            "_",
            " ",
        ) in searchable
        for term in regime_terms
    ):
        return 1.0

    transition = boolean(
        context.get(
            "is_transition"
        )
    )

    candidate_type = text(
        candidate.get(
            "candidate_type"
        )
    )

    if (
        transition
        and candidate_type
        in {
            "FAILURE_MODE_GATE",
            "RESEARCH_PRIORITY",
        }
    ):
        return 0.75

    return 0.35


def score_duplication(
    candidate: dict,
    experiments: pd.DataFrame,
) -> dict:
    if (
        experiments is None
        or experiments.empty
    ):
        return {
            "experiment_id": "",
            "matched_title": "",
            "similarity": 0.0,
            "exact_match": False,
            "status": "NOVEL",
        }

    candidate_text = " ".join([
        text(
            candidate.get(
                "title"
            )
        ),
        text(
            candidate.get(
                "description"
            )
        ),
        text(
            candidate.get(
                "proposed_gate"
            )
        ),
    ])

    best = {
        "experiment_id": "",
        "matched_title": "",
        "similarity": 0.0,
        "exact_match": False,
        "status": "NOVEL",
    }

    for _, row in experiments.iterrows():
        experiment_text = " ".join([
            text(
                row.get("title")
            ),
            text(
                row.get(
                    "description"
                )
            ),
        ])

        similarity = (
            jaccard_similarity(
                candidate_text,
                experiment_text,
            )
        )

        natural_match = (
            text(
                candidate.get(
                    "hypothesis_id"
                )
            )
            and text(
                candidate.get(
                    "hypothesis_id"
                )
            )
            == text(
                row.get(
                    "hypothesis_id"
                )
            )
        )

        exact_match = bool(
            natural_match
            or similarity >= 0.92
        )

        if similarity > best[
            "similarity"
        ] or exact_match:
            best = {
                "experiment_id": text(
                    row.get(
                        "experiment_id"
                    )
                ),
                "matched_title": text(
                    row.get(
                        "title"
                    )
                ),
                "similarity": (
                    1.0
                    if exact_match
                    else similarity
                ),
                "exact_match": (
                    exact_match
                ),
                "status": text(
                    row.get(
                        "current_status"
                    )
                ),
            }

            if exact_match:
                break

    return best


def score_implementation_readiness(
    candidate: dict,
    decisions: pd.DataFrame,
    implementation_queue: pd.DataFrame,
) -> float:
    hypothesis_id = text(
        candidate.get(
            "hypothesis_id"
        )
    )

    engine_id = text(
        candidate.get(
            "parent_engine_id"
        )
    )

    score = 0.20

    for frame in (
        decisions,
        implementation_queue,
    ):
        if frame is None or frame.empty:
            continue

        matching = frame

        if (
            hypothesis_id
            and "hypothesis_id"
            in matching.columns
        ):
            matching = matching[
                matching[
                    "hypothesis_id"
                ].astype(str).eq(
                    hypothesis_id
                )
            ]
        elif (
            engine_id
            and "parent_engine_id"
            in matching.columns
        ):
            matching = matching[
                matching[
                    "parent_engine_id"
                ].astype(str).eq(
                    engine_id
                )
            ]
        else:
            continue

        if matching.empty:
            continue

        score = max(
            score,
            0.65,
        )

        decision_columns = [
            column
            for column in (
                "manual_decision",
                "decision",
                "queue_status",
            )
            if column
            in matching.columns
        ]

        for column in decision_columns:
            values = {
                text(value).upper()
                for value in matching[
                    column
                ]
            }

            if values & {
                "APPROVED",
                "APPROVE",
                "APPROVED_AWAITING_IMPLEMENTATION",
            }:
                score = 1.0

    return clamp(score)


def score_evidence_quality(
    candidate: dict,
) -> float:
    populated = sum(
        bool(
            text(
                candidate.get(key)
            )
        )
        for key in (
            "title",
            "description",
            "parent_engine_id",
            "engine_family",
            "failure_mode",
            "proposed_gate",
            "hypothesis_id",
        )
    )

    return clamp(
        0.20
        + populated / 9.0
    )


def graph_metric_map(
    metrics: pd.DataFrame,
    nodes: pd.DataFrame,
) -> dict:
    if (
        metrics is None
        or metrics.empty
        or nodes is None
        or nodes.empty
    ):
        return {}

    merged = metrics.merge(
        nodes[
            [
                "node_id",
                "natural_key",
                "engine_id",
                "hypothesis_id",
            ]
        ],
        on="node_id",
        how="left",
    )

    max_degree = max(
        [
            number(value)
            for value in merged[
                "total_degree"
            ]
        ],
        default=1.0,
    )

    result = {}

    for _, row in merged.iterrows():
        score = clamp(
            number(
                row.get(
                    "total_degree"
                )
            ) / max(
                1.0,
                max_degree,
            )
        )

        for key in (
            "natural_key",
            "engine_id",
            "hypothesis_id",
        ):
            value = text(
                row.get(key)
            )

            if value:
                result[value] = max(
                    result.get(
                        value,
                        0.0,
                    ),
                    score,
                )

    return result


def failure_recurrence_map(
    frame: pd.DataFrame,
) -> dict:
    if frame is None or frame.empty:
        return {}

    result = {}

    counts = {}

    for _, row in frame.iterrows():
        for key in (
            text(
                row.get(
                    "failure_mode"
                )
            ),
            text(
                row.get(
                    "engine_id"
                )
            ),
        ):
            if key:
                counts[key] = (
                    counts.get(
                        key,
                        0,
                    )
                    + 1
                )

    maximum = max(
        counts.values(),
        default=1,
    )

    for key, count in counts.items():
        result[key] = clamp(
            count / maximum
        )

    return result


def coverage_gap_map(
    frame: pd.DataFrame,
) -> dict:
    if frame is None or frame.empty:
        return {}

    result = {}

    for _, row in frame.iterrows():
        family = text(
            row.get(
                "family",
                row.get(
                    "engine_family",
                    "",
                ),
            )
        )

        if not family:
            continue

        raw = number(
            row.get(
                "gap_score",
                row.get(
                    "coverage_gap",
                    row.get(
                        "priority_score",
                        0.70,
                    ),
                ),
            ),
            default=0.70,
        )

        if raw > 1:
            raw /= 100

        result[family] = clamp(raw)

    return result


def build_coverage_gap_table(
    sources: dict,
) -> pd.DataFrame:
    frame = sources.get(
        "family_gaps",
        pd.DataFrame(),
    )

    if frame is None or frame.empty:
        return pd.DataFrame(
            columns=[
                "engine_family",
                "coverage_gap_score",
                "recommended_research",
            ]
        )

    rows = []

    gap_map = coverage_gap_map(
        frame
    )

    for _, row in frame.iterrows():
        family = text(
            row.get(
                "family",
                row.get(
                    "engine_family",
                    "",
                ),
            )
        )

        rows.append({
            "engine_family": family,
            "coverage_gap_score": (
                gap_map.get(
                    family,
                    0.0,
                )
            ),
            "recommended_research": text(
                row.get(
                    "recommended_research",
                    row.get(
                        "description",
                        "",
                    ),
                )
            ),
        })

    return pd.DataFrame(rows)


def extract_regime_context(
    sources: dict,
) -> dict:
    report = sources.get(
        "regime_report",
        {},
    )

    regime = report.get(
        "regime",
        {},
    )

    return (
        regime
        if isinstance(regime, dict)
        else {}
    )


def classify_band(
    score: float,
    thresholds: dict,
) -> str:
    ordered = sorted(
        thresholds.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    for label, threshold in ordered:
        if score >= threshold:
            return label

    return ordered[-1][0]

