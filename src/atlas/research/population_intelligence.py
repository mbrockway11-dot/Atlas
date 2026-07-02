"""Atlas Population Intelligence.

Analyzes corpus research outputs across many profiles.

This module does not build profiles.
It reads corpus research results and identifies recurring hypotheses,
experiments, falsification cases, validation confidence patterns, and
population-level research priorities.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


POPULATION_INTELLIGENCE_VERSION = "1.0"

DEFAULT_CORPUS_RESEARCH_INDEX = (
    Path("output") / "corpus_research" / "corpus_research_index.json"
)


def build_population_intelligence_payload(
    *,
    index_path: str | Path = DEFAULT_CORPUS_RESEARCH_INDEX,
) -> dict[str, Any]:
    """Build population intelligence payload from corpus research index."""
    path = Path(index_path)

    if not path.exists():
        return missing_index_payload(path)

    model = load_json(path)
    intelligence = build_population_intelligence_model(model)

    return {
        "success": True,
        "version": POPULATION_INTELLIGENCE_VERSION,
        "errors": [],
        "warnings": [],
        "data": {
            "population_intelligence": intelligence,
        },
        "exports": {
            "population_intelligence_json": intelligence,
            "markdown": render_population_intelligence_markdown(intelligence),
        },
        "metrics": build_population_intelligence_metrics(intelligence),
    }


def build_population_intelligence_model(model: dict[str, Any]) -> dict[str, Any]:
    """Build population intelligence model."""
    results = model.get("results", [])

    confidence_bands = build_confidence_bands(results)
    recurring_hypotheses = top_field_counts(results, "best_hypothesis")
    recurring_experiments = top_field_counts(results, "recommended_experiment")
    recurring_falsification = top_field_counts(results, "highest_falsification_case")

    research_priorities = build_population_priorities(
        confidence_bands=confidence_bands,
        recurring_hypotheses=recurring_hypotheses,
        recurring_experiments=recurring_experiments,
        recurring_falsification=recurring_falsification,
        results=results,
    )

    return {
        "version": POPULATION_INTELLIGENCE_VERSION,
        "source_profile_count": model.get("profile_count", len(results)),
        "successful_profiles": model.get("successful_profiles", 0),
        "failed_profiles": model.get("failed_profiles", 0),
        "average_confidence": model.get("average_confidence", {}),
        "confidence_bands": confidence_bands,
        "recurring_hypotheses": recurring_hypotheses,
        "recurring_experiments": recurring_experiments,
        "recurring_falsification_cases": recurring_falsification,
        "validation_summary": {
            "validation_profile_count": model.get("validation_profile_count", 0),
            "memory_recorded_count": model.get("memory_recorded_count", 0),
            "total_next_questions": model.get("total_next_questions", 0),
        },
        "research_priorities": research_priorities,
        "interpretation": build_population_interpretation(
            model=model,
            confidence_bands=confidence_bands,
            recurring_experiments=recurring_experiments,
        ),
    }


def build_confidence_bands(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Build confidence band counts."""
    bands = {
        "high": 0,
        "moderate": 0,
        "limited": 0,
        "low": 0,
        "unknown": 0,
    }

    for result in results:
        label = (
            result.get("overall_confidence", {})
            .get("label", "unknown")
        )

        if label not in bands:
            label = "unknown"

        bands[label] += 1

    total = len(results)

    return {
        "counts": bands,
        "percentages": {
            key: round((value / total) * 100, 2) if total else 0.0
            for key, value in bands.items()
        },
    }


def top_field_counts(
    results: list[dict[str, Any]],
    field: str,
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Count recurring values in one field."""
    counts: dict[str, int] = {}

    for result in results:
        value = result.get(field)

        if not value:
            continue

        text = str(value)
        counts[text] = counts.get(text, 0) + 1

    return [
        {
            "value": value,
            "count": count,
        }
        for value, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[:limit]
    ]


def build_population_priorities(
    *,
    confidence_bands: dict[str, Any],
    recurring_hypotheses: list[dict[str, Any]],
    recurring_experiments: list[dict[str, Any]],
    recurring_falsification: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build population-level research priorities."""
    priorities: list[dict[str, Any]] = []

    counts = confidence_bands.get("counts", {})
    limited_or_low = counts.get("limited", 0) + counts.get("low", 0)

    if limited_or_low > 0:
        priorities.append(
            {
                "title": "Repair Low-Confidence Profiles",
                "priority_type": "confidence_repair",
                "score": limited_or_low,
                "description": (
                    f"{limited_or_low} profile(s) currently have limited or low "
                    "research-cycle confidence."
                ),
                "recommended_followup": [
                    "Inspect recurring warnings.",
                    "Run temporal repair workflows.",
                    "Increase validation-domain coverage.",
                ],
            }
        )

    if recurring_experiments:
        top_experiment = recurring_experiments[0]
        priorities.append(
            {
                "title": "Execute Most Common Recommended Experiment",
                "priority_type": "experiment",
                "score": top_experiment.get("count", 0),
                "description": (
                    f"The most common recommended experiment is: "
                    f"{top_experiment.get('value')}."
                ),
                "recommended_followup": [
                    "Batch the recurring experiment.",
                    "Measure confidence gain before and after execution.",
                ],
            }
        )

    if recurring_falsification:
        top_case = recurring_falsification[0]
        priorities.append(
            {
                "title": "Investigate Recurring Falsification Pressure",
                "priority_type": "falsification",
                "score": top_case.get("count", 0),
                "description": (
                    f"The most common falsification case is: "
                    f"{top_case.get('value')}."
                ),
                "recommended_followup": [
                    "Review shared causes of falsification pressure.",
                    "Determine whether the issue is structural, temporal, or evidential.",
                ],
            }
        )

    if recurring_hypotheses:
        top_hypothesis = recurring_hypotheses[0]
        priorities.append(
            {
                "title": "Study Recurring Best-Supported Hypothesis",
                "priority_type": "hypothesis",
                "score": top_hypothesis.get("count", 0),
                "description": (
                    f"The most common best-supported hypothesis is: "
                    f"{top_hypothesis.get('value')}."
                ),
                "recommended_followup": [
                    "Compare profiles sharing this hypothesis.",
                    "Identify common structural signatures.",
                ],
            }
        )

    if not priorities:
        priorities.append(
            {
                "title": "Expand Corpus Research Sample",
                "priority_type": "sample_expansion",
                "score": len(results),
                "description": "Population intelligence needs more corpus research results.",
                "recommended_followup": [
                    "Run corpus research on additional profiles.",
                    "Add validation domains before drawing population-level claims.",
                ],
            }
        )

    return priorities


def build_population_interpretation(
    *,
    model: dict[str, Any],
    confidence_bands: dict[str, Any],
    recurring_experiments: list[dict[str, Any]],
) -> str:
    """Build population interpretation."""
    profile_count = model.get("profile_count", 0)
    average_confidence = model.get("average_confidence", {})
    counts = confidence_bands.get("counts", {})

    if profile_count == 0:
        return "No corpus research profiles were available for population intelligence."

    limited_or_low = counts.get("limited", 0) + counts.get("low", 0)

    if limited_or_low > counts.get("moderate", 0) + counts.get("high", 0):
        return (
            "Population intelligence indicates that the current corpus research "
            "sample is dominated by limited or low-confidence profiles. The next "
            "research priority should be repair and validation expansion."
        )

    if recurring_experiments:
        return (
            "Population intelligence found recurring recommended experiments, "
            "suggesting shared bottlenecks across the corpus. The strongest next "
            "move is to batch the most common experiment and measure confidence gain."
        )

    return (
        "Population intelligence completed successfully with "
        f"{average_confidence.get('label', 'unknown')} average confidence across "
        f"{profile_count} profile(s)."
    )


def build_population_intelligence_metrics(intelligence: dict[str, Any]) -> dict[str, Any]:
    """Build population intelligence metrics."""
    markdown = render_population_intelligence_markdown(intelligence)

    return {
        "source_profile_count": intelligence.get("source_profile_count", 0),
        "successful_profiles": intelligence.get("successful_profiles", 0),
        "failed_profiles": intelligence.get("failed_profiles", 0),
        "priority_count": len(intelligence.get("research_priorities", [])),
        "recurring_hypothesis_count": len(intelligence.get("recurring_hypotheses", [])),
        "recurring_experiment_count": len(intelligence.get("recurring_experiments", [])),
        "recurring_falsification_count": len(
            intelligence.get("recurring_falsification_cases", [])
        ),
        "average_confidence": intelligence.get("average_confidence", {}),
        "word_count": len(markdown.split()),
    }


def render_population_intelligence_markdown(intelligence: dict[str, Any]) -> str:
    """Render population intelligence as Markdown."""
    average = intelligence.get("average_confidence", {})
    bands = intelligence.get("confidence_bands", {}).get("counts", {})

    lines = [
        "# Atlas Population Intelligence",
        "",
        f"**Version:** {intelligence.get('version', POPULATION_INTELLIGENCE_VERSION)}",
        "",
        "## Summary",
        f"- Source profiles: {intelligence.get('source_profile_count', 0)}",
        f"- Successful profiles: {intelligence.get('successful_profiles', 0)}",
        f"- Failed profiles: {intelligence.get('failed_profiles', 0)}",
        (
            f"- Average confidence: {average.get('percent', 0)}% "
            f"{average.get('label', 'unknown')}"
        ),
        "",
        "## Confidence Bands",
    ]

    for label, count in bands.items():
        lines.append(f"- {label}: {count}")

    lines.append("")
    lines.append("## Top Research Priorities")

    for priority in intelligence.get("research_priorities", []):
        lines.append(
            f"- **{priority.get('title')}** "
            f"({priority.get('priority_type')}): {priority.get('description')}"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append(intelligence.get("interpretation", ""))

    return "\n".join(lines).strip() + "\n"


def missing_index_payload(path: Path) -> dict[str, Any]:
    """Return payload for missing corpus research index."""
    return {
        "success": False,
        "version": POPULATION_INTELLIGENCE_VERSION,
        "errors": [f"Corpus research index not found: {path}"],
        "warnings": [],
        "data": {},
        "exports": {},
        "metrics": {
            "source_profile_count": 0,
            "priority_count": 0,
        },
    }


def load_json(path: Path) -> dict[str, Any]:
    """Load JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def json_export(data: Any) -> str:
    """Serialize JSON."""
    return json.dumps(data, indent=2, sort_keys=True)