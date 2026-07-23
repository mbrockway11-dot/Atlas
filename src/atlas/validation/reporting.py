"""Human-readable reports for validation experiments.

Reports state what was measured, against which corpus, and what the numbers
do *not* license. For identity-vector experiments that includes an explicit
statement that no temporal claim is supported, because the vectors are
name-derived and a reader should not have to know that to read the report
correctly.
"""

from __future__ import annotations

from typing import Any

from atlas.validation.models import ExperimentConfig, ExperimentDomain
from atlas.validation.statistics import DistributionSummary


DOMAIN_SCOPE_NOTES = {
    ExperimentDomain.IDENTITY_VECTOR: (
        "Identity vectors are derived from the name alone. Nothing in this "
        "report supports any claim about birth data, dates, or temporal "
        "structure. Any group effect seen here is a property of naming -- "
        "conventions, transliteration, length, or the symbolic encoding -- "
        "and not evidence that a real-world relationship enters the vector."
    ),
    ExperimentDomain.TEMPORAL_CSS: (
        "Temporal/CSS outputs depend on birth and evaluation dates. Transit "
        "geometry compiled into CSS uses a fixed placeholder epoch and must "
        "not be read as current transits."
    ),
    ExperimentDomain.RELATIONSHIP: (
        "Relationship cohorts inherit the constraints of whichever model "
        "produced their scores. Check the domain of the underlying metric "
        "before drawing conclusions."
    ),
    ExperimentDomain.COMBINED: (
        "This experiment spans models with different inputs. State which "
        "component any effect is attributed to."
    ),
}


def _fmt(value: float, places: int = 6) -> str:
    """Format a float for a report table."""
    return f"{value:.{places}f}"


def render_baseline_report(
    *,
    config: ExperimentConfig,
    provenance: dict[str, Any],
    summary: DistributionSummary,
    extremes: dict[str, Any],
    strata: dict[str, Any],
    confounders: list[dict[str, Any]],
    group_summaries: dict[str, dict[str, Any]],
    elapsed_seconds: float,
    skipped: list[str],
) -> str:
    """Render the all-pairs baseline report as Markdown."""
    corpus = provenance["corpus"]
    build = provenance["build"]

    lines: list[str] = []

    lines.append(f"# {config.experiment_id}")
    lines.append("")
    lines.append(f"**Domain:** `{config.domain.value}` — "
                 f"**Kind:** `{config.kind.value}`")
    lines.append("")
    lines.append("## Hypothesis")
    lines.append("")
    lines.append(config.hypothesis.strip())
    lines.append("")

    lines.append("## Scope and limits")
    lines.append("")
    lines.append(DOMAIN_SCOPE_NOTES[config.domain])
    lines.append("")

    lines.append("## Corpus")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    lines.append(f"| Profiles | {corpus['profile_count']:,} |")
    lines.append(f"| Pairs | {corpus['pair_count']:,} |")
    lines.append(f"| Normalization | `{corpus['normalization_mode']}` |")
    lines.append(f"| Metric | `{config.metric}` |")
    lines.append(f"| Feature schema | `{corpus['feature_schema_hash'][:16]}…` |")
    lines.append(f"| Source manifest | `{corpus['source_manifest_hash'][:16]}…` |")
    lines.append(f"| Artifact schema | `{corpus['artifact_schema_version']}` |")
    lines.append(f"| Compiler | {build['compiler_version']} "
                 f"({build['git_commit']}"
                 f"{', dirty' if build['git_dirty'] else ''}) |")
    lines.append(f"| Elapsed | {elapsed_seconds:.2f}s |")
    lines.append("")

    if skipped:
        lines.append(
            f"{len(skipped)} profile(s) were skipped for incomplete feature "
            f"coverage: {', '.join(skipped[:10])}"
            + (" …" if len(skipped) > 10 else "")
        )
        lines.append("")

    if confounders:
        strongest = confounders[0]
        lines.append("## Confounders")
        lines.append("")
        lines.append(
            "Measured before any cohort study, because a cohort whose names "
            "share a shape would otherwise score high for reasons that have "
            "nothing to do with the cohort."
        )
        lines.append("")
        lines.append("| Variable | Pearson r | Variance explained |")
        lines.append("|---|---|---|")
        for row in confounders:
            lines.append(
                f"| {row['variable']} | {row['pearson_r']:+.4f} "
                f"| {row['variance_explained']:.1%} |"
            )
        lines.append("")
        lines.append(
            f"**The dominant confounder is {strongest['variable']} "
            f"(r = {strongest['pearson_r']:+.4f}, "
            f"{strongest['variance_explained']:.0%} of variance).** Any "
            "experiment comparing cohorts must match or stratify controls "
            "on it; otherwise a difference in name shape will be reported "
            "as a difference in identity structure."
        )
        lines.append("")

    lines.append("## Score distribution")
    lines.append("")
    lines.append("| Statistic | Value |")
    lines.append("|---|---|")
    lines.append(f"| Count | {summary.count:,} |")
    lines.append(f"| Mean | {_fmt(summary.mean)} |")
    lines.append(f"| Median | {_fmt(summary.median)} |")
    lines.append(f"| Std dev | {_fmt(summary.stddev)} |")
    lines.append(f"| Min | {_fmt(summary.minimum)} |")
    lines.append(f"| Max | {_fmt(summary.maximum)} |")
    lines.append(f"| Skewness | {_fmt(summary.skewness, 4)} |")
    lines.append(f"| Excess kurtosis | {_fmt(summary.kurtosis, 4)} |")
    lines.append(f"| Distinct scores | {summary.distinct_scores:,} |")
    lines.append(
        f"| Duplicate-score fraction | {_fmt(summary.duplicate_score_fraction, 6)} |"
    )
    lines.append("")

    lines.append("### Percentiles")
    lines.append("")
    lines.append("| Percentile | Score |")
    lines.append("|---|---|")
    for label, value in summary.percentiles.items():
        lines.append(f"| {label} | {_fmt(value)} |")
    lines.append("")

    if group_summaries:
        lines.append("## Per-cipher and per-planet distributions")
        lines.append("")
        lines.append("Computed on a deterministic sample of pairs.")
        lines.append("")
        lines.append("| Group | Mean | Median | Std dev | Min | Max |")
        lines.append("|---|---|---|---|---|---|")
        for label in sorted(group_summaries):
            g = group_summaries[label]
            lines.append(
                f"| `{label}` | {_fmt(g['mean'], 4)} | {_fmt(g['median'], 4)} "
                f"| {_fmt(g['stddev'], 4)} | {_fmt(g['minimum'], 4)} "
                f"| {_fmt(g['maximum'], 4)} |"
            )
        lines.append("")

    if strata:
        lines.append("## Stratified means")
        lines.append("")
        lines.append(
            "Exposes confounders before any cohort study: if similarity "
            "tracks name shape, that must be visible here rather than "
            "discovered inside a substantive result."
        )
        lines.append("")
        for name, rows in strata.items():
            lines.append(f"### {name}")
            lines.append("")
            lines.append("| Stratum | Pairs | Mean | Std dev |")
            lines.append("|---|---|---|---|")
            for row in rows:
                lines.append(
                    f"| {row['stratum']} | {row['count']:,} | "
                    f"{_fmt(row['mean'], 4)} | {_fmt(row['stddev'], 4)} |"
                )
            lines.append("")

    lines.append("## Extremes")
    lines.append("")
    for heading, key in (("Highest-scoring pairs", "top"),
                         ("Lowest-scoring pairs", "bottom")):
        lines.append(f"### {heading}")
        lines.append("")
        lines.append("| Profile A | Profile B | Score |")
        lines.append("|---|---|---|")
        for row in extremes.get(key, [])[:15]:
            lines.append(
                f"| {row['profile_a']} | {row['profile_b']} "
                f"| {_fmt(row['score'])} |"
            )
        lines.append("")

    lines.append("## How to read a score")
    lines.append("")
    lines.append(
        "The deterministic score and its population percentile are separate "
        "quantities. A high score is not by itself evidence of anything: it "
        "becomes meaningful only relative to this distribution, and only "
        "against a matched control."
    )
    lines.append("")

    return "\n".join(lines)
