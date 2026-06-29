"""Translation fusion metrics.

Translation fusion measures agreement between the independent cipher streams
for each planetary graph. It does not replace the Identity Vector Engine; it
adds confidence and agreement information above the existing 21-layer analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pvariance
from typing import Any


EXPECTED_CIPHERS = {
    "ordinal",
    "hebrew_literal",
    "hebrew_phonetic",
}


@dataclass(frozen=True)
class PlanetTranslationFusion:
    """Translation fusion for one planet."""

    planet: str
    source_ciphers: list[str]
    feature_means: dict[str, float]
    feature_variance: dict[str, float]
    feature_agreement: dict[str, float]
    agreement_score: float
    confidence_score: float
    completeness: float


@dataclass(frozen=True)
class TranslationFusionReport:
    """Translation fusion report for an identity."""

    name: str
    planets: dict[str, PlanetTranslationFusion]
    global_agreement_score: float
    global_confidence_score: float
    global_completeness: float


def build_translation_fusion_report(
    acf: dict[str, Any],
) -> TranslationFusionReport:
    """Build translation fusion report from an ACF profile."""
    name = acf.get("identity", {}).get("name", "Unknown")

    analyses = acf.get("invariant_analysis", {}).get("analyses", [])

    grouped = group_analyses_by_planet(analyses)

    planet_reports = {
        planet: build_planet_translation_fusion(
            planet=planet,
            analyses=planet_analyses,
        )
        for planet, planet_analyses in grouped.items()
    }

    global_agreement = average(
        [
            report.agreement_score
            for report in planet_reports.values()
        ]
    )

    global_confidence = average(
        [
            report.confidence_score
            for report in planet_reports.values()
        ]
    )

    global_completeness = average(
        [
            report.completeness
            for report in planet_reports.values()
        ]
    )

    return TranslationFusionReport(
        name=name,
        planets=planet_reports,
        global_agreement_score=global_agreement,
        global_confidence_score=global_confidence,
        global_completeness=global_completeness,
    )


def group_analyses_by_planet(
    analyses: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group invariant analyses by planet."""
    grouped: dict[str, list[dict[str, Any]]] = {}

    for analysis in analyses:
        planet = analysis.get("planet")

        if not planet:
            continue

        grouped.setdefault(planet, [])
        grouped[planet].append(analysis)

    return grouped


def build_planet_translation_fusion(
    planet: str,
    analyses: list[dict[str, Any]],
) -> PlanetTranslationFusion:
    """Build translation fusion metrics for one planet."""
    source_ciphers = sorted(
        {
            analysis.get("cipher", "")
            for analysis in analyses
            if analysis.get("cipher")
        }
    )

    features_by_cipher = {
        analysis["cipher"]: extract_numeric_analysis_features(analysis)
        for analysis in analyses
        if analysis.get("cipher")
    }

    feature_names = sorted(
        {
            feature
            for feature_map in features_by_cipher.values()
            for feature in feature_map
        }
    )

    feature_means = {}
    feature_variance = {}
    feature_agreement = {}

    for feature in feature_names:
        values = [
            feature_map[feature]
            for feature_map in features_by_cipher.values()
            if feature in feature_map
        ]

        if not values:
            continue

        feature_mean = mean(values)
        variance = pvariance(values) if len(values) > 1 else 0.0

        feature_means[feature] = float(feature_mean)
        feature_variance[feature] = float(variance)
        feature_agreement[feature] = variance_to_agreement(variance)

    agreement_score = average(list(feature_agreement.values()))
    completeness = len(source_ciphers) / len(EXPECTED_CIPHERS)
    confidence_score = agreement_score * completeness

    return PlanetTranslationFusion(
        planet=planet,
        source_ciphers=source_ciphers,
        feature_means=feature_means,
        feature_variance=feature_variance,
        feature_agreement=feature_agreement,
        agreement_score=agreement_score,
        confidence_score=confidence_score,
        completeness=completeness,
    )


def extract_numeric_analysis_features(
    analysis: dict[str, Any],
) -> dict[str, float]:
    """Extract numeric scalar features from one 21-layer analysis."""
    signature = analysis.get("signature", {})

    features: dict[str, float] = {}

    for section in [
        "scores",
        "metrics",
        "motifs",
    ]:
        values = signature.get(section, {})

        for key, value in values.items():
            if isinstance(value, int | float):
                features[key] = float(value)

    invariant = analysis.get("invariant_features", {})

    for key, value in invariant.items():
        if isinstance(value, int | float):
            features[key] = float(value)

    return features


def variance_to_agreement(
    variance: float,
) -> float:
    """Convert variance to 0-1 agreement score."""
    return 1.0 / (1.0 + max(0.0, float(variance)))


def average(values: list[float]) -> float:
    """Average values safely."""
    if not values:
        return 0.0

    return float(sum(values) / len(values))


def planet_translation_fusion_to_dict(
    fusion: PlanetTranslationFusion,
) -> dict[str, Any]:
    """Convert planet fusion to dict."""
    return {
        "planet": fusion.planet,
        "source_ciphers": fusion.source_ciphers,
        "feature_means": fusion.feature_means,
        "feature_variance": fusion.feature_variance,
        "feature_agreement": fusion.feature_agreement,
        "agreement_score": fusion.agreement_score,
        "confidence_score": fusion.confidence_score,
        "completeness": fusion.completeness,
    }


def translation_fusion_report_to_dict(
    report: TranslationFusionReport,
) -> dict[str, Any]:
    """Convert fusion report to dict."""
    return {
        "name": report.name,
        "global_agreement_score": report.global_agreement_score,
        "global_confidence_score": report.global_confidence_score,
        "global_completeness": report.global_completeness,
        "planets": {
            planet: planet_translation_fusion_to_dict(fusion)
            for planet, fusion in report.planets.items()
        },
    }