"""Markdown report generation for Atlas profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.acf.builder import build_acf_profile
from atlas.interpretation.profile import ProfileInterpretation
from atlas.ive import (
    build_identity_vector,
    build_planet_relationship_matrix,
)


def build_profile_markdown_report(
    summary: dict[str, Any],
    interpretation: ProfileInterpretation,
) -> str:
    """Build a human-readable Atlas Codex markdown report.

    The report now prioritizes the Identity Vector Engine.
    Legacy driver/amplifier/regulator language is no longer used as the primary
    report structure.
    """
    name = summary["name"]
    acf = build_acf_profile(name)
    identity_vector = build_identity_vector(
        acf,
        normalization_mode="raw",
    )
    relationship_matrix = build_planet_relationship_matrix(identity_vector)

    lines: list[str] = []

    lines.append(f"# Atlas Codex Report: {name}")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(
        "This report is generated from the Atlas Identity Vector Engine. "
        "Graphs are treated as measurement instruments; the Identity Vector is "
        "the canonical structural representation."
    )
    lines.append("")

    lines.extend(_identity_summary(identity_vector))
    lines.extend(_planetary_signature(identity_vector))
    lines.extend(_relationship_diagnostics(relationship_matrix))
    lines.extend(_vector_quality(identity_vector))
    lines.extend(_legacy_interpretation_summary(interpretation))
    lines.extend(_legacy_layer_archive(summary))

    return "\n".join(lines)


def write_markdown_report(report: str, output_path: str | Path) -> Path:
    """Write markdown report to disk."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    return path


def _identity_summary(identity_vector) -> list[str]:
    """Build Identity Vector summary section."""
    features = identity_vector.global_features
    diagnostics = identity_vector.diagnostics

    return [
        "## Identity Vector Summary",
        "",
        f"- Balance Index: **{features['planet_balance_index']:.4f}**",
        f"- Planet Variance Index: **{features['planet_variance_index']:.4f}**",
        f"- Structural Complexity Index: **{features['structural_complexity_index']:.4f}**",
        f"- Structural Stability Index: **{features['structural_stability_index']:.4f}**",
        f"- Mean Graph Coherence: **{features['mean_graph_coherence']:.4f}**",
        f"- Mean Entropy: **{features['mean_entropy']:.4f}**",
        f"- Mean Node Coverage: **{features['mean_node_coverage']:.4f}**",
        f"- Mean Edge Coverage: **{features['mean_edge_coverage']:.4f}**",
        "",
        "### Dominant Structural Signals",
        "",
        f"- Dominant Coherence Planet: **{diagnostics['dominant_coherence_planet']}**",
        f"- Weakest Coherence Planet: **{diagnostics['weakest_coherence_planet']}**",
        f"- Dominant Stability Planet: **{diagnostics['dominant_stability_planet']}**",
        f"- Weakest Stability Planet: **{diagnostics['weakest_stability_planet']}**",
        f"- Dominant Entropy Planet: **{diagnostics['dominant_entropy_planet']}**",
        f"- Weakest Entropy Planet: **{diagnostics['weakest_entropy_planet']}**",
        "",
    ]


def _planetary_signature(identity_vector) -> list[str]:
    """Build planetary structural signature section."""
    lines = [
        "## Planetary Structural Signature",
        "",
    ]

    for planet, vector in identity_vector.planets.items():
        features = vector.features

        lines.extend(
            [
                f"### {planet}",
                "",
                f"- Graph Coherence: **{features['graph_coherence']:.4f}**",
                f"- Attractor Stability: **{features['attractor_stability']:.4f}**",
                f"- Topology Stability: **{features['topology_stability']:.4f}**",
                f"- Core Survival Score: **{features['core_survival_score']:.4f}**",
                f"- Entropy: **{features['entropy']:.4f}**",
                f"- Density: **{features['density']:.4f}**",
                f"- Node Coverage: **{features['node_coverage']:.4f}**",
                f"- Edge Coverage: **{features['edge_coverage']:.4f}**",
                f"- Bridge Ratio: **{features['bridge_ratio']:.4f}**",
                f"- Loop Ratio: **{features['loop_ratio']:.4f}**",
                f"- Hub Ratio: **{features['hub_ratio']:.4f}**",
                f"- Leaf Ratio: **{features['leaf_ratio']:.4f}**",
                f"- Reduction Entropy: **{features['reduction_entropy']:.4f}**",
                f"- Source Ciphers: **{', '.join(vector.source_ciphers)}**",
                "",
            ]
        )

    return lines


def _relationship_diagnostics(matrix) -> list[str]:
    """Build relationship matrix diagnostics section."""
    diagnostics = matrix.diagnostics

    lines = [
        "## Planet Relationship Diagnostics",
        "",
        f"- Pair Count: **{diagnostics['pair_count']}**",
        f"- Mean Similarity: **{diagnostics['mean_similarity']:.4f}**",
        f"- Mean Distance: **{diagnostics['mean_distance']:.4f}**",
        f"- Mean Agreement: **{diagnostics['mean_agreement']:.4f}**",
        "",
    ]

    strongest = diagnostics.get("strongest_pair")
    weakest = diagnostics.get("weakest_pair")
    divergent = diagnostics.get("most_divergent_pair")

    if strongest:
        lines.extend(_relationship_pair_block("Strongest Planet Pair", strongest))

    if weakest:
        lines.extend(_relationship_pair_block("Weakest Planet Pair", weakest))

    if divergent:
        lines.extend(_relationship_pair_block("Most Divergent Planet Pair", divergent))

    return lines


def _relationship_pair_block(label: str, pair: dict[str, Any]) -> list[str]:
    """Build markdown for one relationship pair."""
    return [
        f"### {label}",
        "",
        f"- Pair: **{pair['planet_a']} ↔ {pair['planet_b']}**",
        f"- Similarity: **{pair['similarity']:.4f}**",
        f"- Distance: **{pair['distance']:.4f}**",
        f"- Agreement: **{pair['agreement']:.4f}**",
        "",
    ]


def _vector_quality(identity_vector) -> list[str]:
    """Build vector quality section."""
    quality = identity_vector.quality

    return [
        "## Vector Quality",
        "",
        f"- Planet Count: **{quality['planet_count']} / {quality['expected_planet_count']}**",
        f"- Completeness: **{quality['completeness']:.4f}**",
        f"- Mean Source Count: **{quality['mean_source_count']:.4f} / {quality['expected_source_count']}**",
        f"- Source Completeness: **{quality['source_completeness']:.4f}**",
        f"- Normalization Mode: **{quality['normalization_mode']}**",
        f"- Mean Calibration Size: **{quality['mean_calibration_size']:.4f}**",
        f"- Minimum Calibration Size: **{quality['minimum_calibration_size']}**",
        "",
    ]


def _legacy_interpretation_summary(
    interpretation: ProfileInterpretation,
) -> list[str]:
    """Keep legacy motif/pattern summaries as an archived reference."""
    lines = [
        "## Legacy Pattern Archive",
        "",
        "These pattern and motif summaries are retained for continuity. "
        "They are no longer the primary report structure.",
        "",
        "### Dominant Patterns",
        "",
    ]

    for pattern, count in interpretation.dominant_patterns.items():
        lines.append(f"- **{pattern}**: {count}")

    lines.extend(
        [
            "",
            "### Dominant Motifs",
            "",
        ]
    )

    for motif, count in interpretation.dominant_motifs.items():
        lines.append(f"- **{motif}**: {count}")

    lines.append("")

    return lines


def _legacy_layer_archive(summary: dict[str, Any]) -> list[str]:
    """Keep old 21-layer details as an archived section if available."""
    analyses = summary.get("analyses", [])

    if not analyses:
        return []

    lines = [
        "## Legacy 21-Layer Archive",
        "",
        "This section preserves older layer summaries for historical continuity.",
        "",
    ]

    for analysis in analyses:
        lines.extend(_legacy_analysis_section(analysis))

    return lines


def _legacy_analysis_section(analysis: dict[str, Any]) -> list[str]:
    """Build archived markdown section for one old analysis record."""
    signature = analysis.get("signature", {})
    metrics = signature.get("metrics", {})
    patterns = signature.get("patterns", {})
    motifs = signature.get("motifs", {})

    return [
        f"### {analysis.get('planet', 'Unknown')} / {analysis.get('cipher', 'unknown')}",
        "",
        f"- Kamea: **{analysis.get('kamea', 'unknown')}**",
        f"- Nodes: **{metrics.get('node_count', 'n/a')}**",
        f"- Edges: **{metrics.get('edge_count', 'n/a')}**",
        f"- Edge Density: **{format_metric(metrics.get('edge_density'))}**",
        f"- Symmetry: **{format_metric(metrics.get('symmetry'))}**",
        f"- Entropy: **{format_metric(metrics.get('entropy'))}**",
        f"- Dominant Pattern: **{patterns.get('dominant_pattern', 'n/a')}**",
        f"- Branching: **{patterns.get('branching_level', 'n/a')}**",
        f"- Reciprocity: **{patterns.get('reciprocity_level', 'n/a')}**",
        f"- Compression: **{patterns.get('compression_level', 'n/a')}**",
        f"- Dominant Motif: **{motifs.get('dominant_motif', 'n/a')}**",
        f"- Chains: **{motifs.get('chains', 'n/a')}**",
        f"- Hubs: **{motifs.get('hubs', 'n/a')}**",
        f"- Loops: **{motifs.get('loops', 'n/a')}**",
        f"- Bridges: **{motifs.get('bridges', 'n/a')}**",
        "",
    ]


def format_metric(value) -> str:
    """Format optional metric safely."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"