
"""Evidence fusion for Atlas Synthesis."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any

from atlas.synthesis.evidence import EvidenceBundle, StructuralEvidence
from atlas.synthesis.ontology import describe_category, describe_feature


SYNTHESIS_FUSION_VERSION = "1.0"


@dataclass(frozen=True)
class FusedTheme:
    """Evidence fused into one structural theme."""

    feature: str
    category: str
    evidence_count: int
    engine_count: int
    support_score: float
    average_confidence: float
    weighted_confidence: float
    consensus_score: float
    value_samples: tuple[Any, ...]
    engines: tuple[str, ...]
    explanations: tuple[str, ...]


@dataclass(frozen=True)
class SynthesisFusionResult:
    """Fused evidence result for one profile."""

    version: str
    profile_key: str
    evidence_count: int
    theme_count: int
    categories: dict[str, list[FusedTheme]]
    themes: tuple[FusedTheme, ...]
    strongest_themes: tuple[FusedTheme, ...]


def fuse_evidence_bundle(bundle: EvidenceBundle) -> SynthesisFusionResult:
    """Fuse an evidence bundle into theme consensus records."""

    grouped: dict[str, list[StructuralEvidence]] = {}

    for item in bundle.evidence:
        grouped.setdefault(item.feature, []).append(item)

    themes = tuple(
        sorted(
            [
                fuse_feature(feature, records)
                for feature, records in grouped.items()
            ],
            key=lambda item: item.consensus_score,
            reverse=True,
        )
    )

    categories: dict[str, list[FusedTheme]] = {}

    for theme in themes:
        categories.setdefault(theme.category, []).append(theme)

    return SynthesisFusionResult(
        version=SYNTHESIS_FUSION_VERSION,
        profile_key=bundle.profile_key,
        evidence_count=len(bundle.evidence),
        theme_count=len(themes),
        categories=categories,
        themes=themes,
        strongest_themes=themes[:10],
    )


def fuse_feature(
    feature: str,
    records: list[StructuralEvidence],
) -> FusedTheme:
    """Fuse records for one feature."""

    if not records:
        return FusedTheme(
            feature=feature,
            category="unknown",
            evidence_count=0,
            engine_count=0,
            support_score=0.0,
            average_confidence=0.0,
            weighted_confidence=0.0,
            consensus_score=0.0,
            value_samples=(),
            engines=(),
            explanations=(),
        )

    category = records[0].category

    engines = tuple(sorted({item.engine for item in records}))
    weights = [max(0.0, float(item.weight)) for item in records]
    confidences = [clamp(item.confidence) for item in records]

    total_weight = sum(weights) or 1.0

    weighted_confidence = sum(
        confidence * weight
        for confidence, weight in zip(confidences, weights)
    ) / total_weight

    average_confidence = sum(confidences) / len(confidences)

    support_score = min(1.0, len(engines) / 5.0)

    consensus_score = (
        weighted_confidence * 0.70
        + support_score * 0.30
    )

    value_samples = tuple(
        item.value
        for item in records[:6]
    )

    explanations = tuple(
        item.explanation
        for item in records
        if item.explanation
    )[:8]

    return FusedTheme(
        feature=feature,
        category=category,
        evidence_count=len(records),
        engine_count=len(engines),
        support_score=round(support_score, 6),
        average_confidence=round(average_confidence, 6),
        weighted_confidence=round(weighted_confidence, 6),
        consensus_score=round(consensus_score, 6),
        value_samples=value_samples,
        engines=engines,
        explanations=explanations,
    )


def fusion_result_to_dict(result: SynthesisFusionResult) -> dict[str, Any]:
    """Convert fusion result to JSON-safe dict."""
    return {
        "version": result.version,
        "profile_key": result.profile_key,
        "evidence_count": result.evidence_count,
        "theme_count": result.theme_count,
        "strongest_themes": [
            fused_theme_to_dict(item)
            for item in result.strongest_themes
        ],
        "themes": [
            fused_theme_to_dict(item)
            for item in result.themes
        ],
        "categories": {
            category: [
                fused_theme_to_dict(item)
                for item in themes
            ]
            for category, themes in result.categories.items()
        },
    }


def fused_theme_to_dict(theme: FusedTheme) -> dict[str, Any]:
    """Convert fused theme to JSON-safe dict."""
    data = asdict(theme)
    data["value_samples"] = list(theme.value_samples)
    data["engines"] = list(theme.engines)
    data["explanations"] = list(theme.explanations)
    data["feature_description"] = describe_feature(theme.feature)
    data["category_description"] = describe_category(theme.category)
    return data


def clamp(value: Any, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Clamp float value."""
    try:
        numeric = float(value)
    except Exception:
        numeric = 0.0

    return max(minimum, min(maximum, numeric))
