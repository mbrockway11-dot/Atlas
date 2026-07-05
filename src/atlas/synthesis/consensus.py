
"""Consensus scoring for Atlas Synthesis."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any

from atlas.synthesis.fusion import FusedTheme, SynthesisFusionResult, fused_theme_to_dict


SYNTHESIS_CONSENSUS_VERSION = "1.0"


@dataclass(frozen=True)
class ConsensusReport:
    """Consensus report for fused synthesis themes."""

    version: str
    profile_key: str
    theme_count: int
    dominant_themes: tuple[FusedTheme, ...]
    strong_themes: tuple[FusedTheme, ...]
    moderate_themes: tuple[FusedTheme, ...]
    weak_themes: tuple[FusedTheme, ...]
    single_source_themes: tuple[FusedTheme, ...]
    category_summary: dict[str, dict[str, Any]]


def build_consensus_report(fusion: SynthesisFusionResult) -> ConsensusReport:
    """Classify fused themes by consensus strength."""

    dominant = []
    strong = []
    moderate = []
    weak = []
    single_source = []

    for theme in fusion.themes:
        if theme.engine_count == 1:
            single_source.append(theme)

        if theme.consensus_score >= 0.80 and theme.engine_count >= 2:
            dominant.append(theme)
        elif theme.consensus_score >= 0.68:
            strong.append(theme)
        elif theme.consensus_score >= 0.50:
            moderate.append(theme)
        else:
            weak.append(theme)

    return ConsensusReport(
        version=SYNTHESIS_CONSENSUS_VERSION,
        profile_key=fusion.profile_key,
        theme_count=fusion.theme_count,
        dominant_themes=tuple(dominant),
        strong_themes=tuple(strong),
        moderate_themes=tuple(moderate),
        weak_themes=tuple(weak),
        single_source_themes=tuple(single_source),
        category_summary=build_category_summary(fusion),
    )


def build_category_summary(fusion: SynthesisFusionResult) -> dict[str, dict[str, Any]]:
    """Build per-category consensus summary."""

    output: dict[str, dict[str, Any]] = {}

    for category, themes in fusion.categories.items():
        if not themes:
            continue

        scores = [theme.consensus_score for theme in themes]
        evidence_count = sum(theme.evidence_count for theme in themes)
        engine_count = len({engine for theme in themes for engine in theme.engines})

        strongest = max(themes, key=lambda item: item.consensus_score)

        output[category] = {
            "theme_count": len(themes),
            "evidence_count": evidence_count,
            "engine_count": engine_count,
            "average_consensus": round(sum(scores) / len(scores), 6),
            "max_consensus": round(max(scores), 6),
            "strongest_theme": strongest.feature,
            "strongest_theme_score": strongest.consensus_score,
        }

    return output


def consensus_report_to_dict(report: ConsensusReport) -> dict[str, Any]:
    """Convert consensus report to JSON-safe dict."""

    return {
        "version": report.version,
        "profile_key": report.profile_key,
        "theme_count": report.theme_count,
        "dominant_themes": [
            fused_theme_to_dict(theme)
            for theme in report.dominant_themes
        ],
        "strong_themes": [
            fused_theme_to_dict(theme)
            for theme in report.strong_themes
        ],
        "moderate_themes": [
            fused_theme_to_dict(theme)
            for theme in report.moderate_themes
        ],
        "weak_themes": [
            fused_theme_to_dict(theme)
            for theme in report.weak_themes
        ],
        "single_source_themes": [
            fused_theme_to_dict(theme)
            for theme in report.single_source_themes
        ],
        "category_summary": report.category_summary,
    }


def strongest_theme_names(report: ConsensusReport, limit: int = 5) -> list[str]:
    """Return strongest theme names in priority order."""

    themes = (
        list(report.dominant_themes)
        + list(report.strong_themes)
        + list(report.moderate_themes)
    )

    themes = sorted(
        themes,
        key=lambda item: item.consensus_score,
        reverse=True,
    )

    return [
        theme.feature
        for theme in themes[:limit]
    ]


def consensus_label(theme: FusedTheme) -> str:
    """Return label for one theme."""

    if theme.consensus_score >= 0.80 and theme.engine_count >= 2:
        return "dominant_consensus"

    if theme.consensus_score >= 0.68:
        return "strong_consensus"

    if theme.consensus_score >= 0.50:
        return "moderate_consensus"

    return "weak_consensus"
