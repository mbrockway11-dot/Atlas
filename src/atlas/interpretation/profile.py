"""Profile-level interpretation utilities."""

from collections import Counter
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProfileInterpretation:
    """Deterministic profile interpretation."""

    name: str
    analysis_count: int
    dominant_patterns: dict[str, int]
    dominant_motifs: dict[str, int]
    strongest_driver: dict[str, Any]
    strongest_amplifier: dict[str, Any]
    strongest_regulator: dict[str, Any]
    summary_lines: list[str]


def interpret_profile_summary(summary: dict[str, Any]) -> ProfileInterpretation:
    """Interpret an Atlas profile summary JSON object."""
    analyses = summary["analyses"]

    pattern_counts = Counter()
    motif_counts = Counter()

    for analysis in analyses:
        pattern_counts[analysis["signature"]["patterns"]["dominant_pattern"]] += 1
        motif_counts[analysis["signature"]["motifs"]["dominant_motif"]] += 1

    strongest_driver = _strongest_score(analyses, "driver")
    strongest_amplifier = _strongest_score(analyses, "amplifier")
    strongest_regulator = _strongest_score(analyses, "regulator")

    summary_lines = [
        f"Profile contains {len(analyses)} deterministic analyses.",
        _dominant_pattern_line(pattern_counts),
        _dominant_motif_line(motif_counts),
        _score_line("Strongest driver", strongest_driver),
        _score_line("Strongest amplifier", strongest_amplifier),
        _score_line("Strongest regulator", strongest_regulator),
    ]

    return ProfileInterpretation(
        name=summary["name"],
        analysis_count=len(analyses),
        dominant_patterns=dict(pattern_counts),
        dominant_motifs=dict(motif_counts),
        strongest_driver=strongest_driver,
        strongest_amplifier=strongest_amplifier,
        strongest_regulator=strongest_regulator,
        summary_lines=summary_lines,
    )


def profile_interpretation_to_dict(
    interpretation: ProfileInterpretation,
) -> dict[str, Any]:
    """Convert profile interpretation to JSON-safe dictionary."""
    return {
        "name": interpretation.name,
        "analysis_count": interpretation.analysis_count,
        "dominant_patterns": interpretation.dominant_patterns,
        "dominant_motifs": interpretation.dominant_motifs,
        "strongest_driver": interpretation.strongest_driver,
        "strongest_amplifier": interpretation.strongest_amplifier,
        "strongest_regulator": interpretation.strongest_regulator,
        "summary_lines": interpretation.summary_lines,
    }


def _strongest_score(
    analyses: list[dict[str, Any]],
    score_name: str,
) -> dict[str, Any]:
    """Find analysis with strongest score."""
    best = max(
        analyses,
        key=lambda analysis: analysis["signature"]["scores"][score_name],
    )

    return {
        "cipher": best["cipher"],
        "kamea": best["kamea"],
        "planet": best["planet"],
        "score": best["signature"]["scores"][score_name],
        "dominant_pattern": best["signature"]["patterns"]["dominant_pattern"],
        "dominant_motif": best["signature"]["motifs"]["dominant_motif"],
    }


def _dominant_pattern_line(pattern_counts: Counter) -> str:
    """Create dominant pattern summary line."""
    pattern, count = pattern_counts.most_common(1)[0]
    return f"Most common pattern is {pattern}, appearing {count} times."


def _dominant_motif_line(motif_counts: Counter) -> str:
    """Create dominant motif summary line."""
    motif, count = motif_counts.most_common(1)[0]
    return f"Most common motif is {motif}, appearing {count} times."


def _score_line(label: str, score_data: dict[str, Any]) -> str:
    """Create strongest score summary line."""
    return (
        f"{label}: {score_data['planet']} / {score_data['cipher']} "
        f"at {score_data['score']:.4f} "
        f"({score_data['dominant_pattern']} / {score_data['dominant_motif']})."
    )