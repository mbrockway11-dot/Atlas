
"""Benchmark expanded Atlas population corpus.

Writes:
- output/benchmarks/expanded_population_benchmark.json
- output/benchmarks/expanded_population_benchmark.md
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from atlas.autonomous.director import build_director_report
from atlas.library.profile_library import list_saved_profiles
from atlas.services.discovery_service import build_discovery_records


OUT_DIR = Path("output/benchmarks")
JSON_PATH = OUT_DIR / "expanded_population_benchmark.json"
MD_PATH = OUT_DIR / "expanded_population_benchmark.md"


def build_expanded_population_benchmark(
    *,
    max_schedule_items: int = 5,
    export: bool = True,
) -> dict[str, Any]:
    """Run expanded population benchmark."""
    started = time.time()

    print('Loading compiled profiles...', flush=True)
    profiles = list_saved_profiles()
    print(f'Loaded profiles: {len(profiles)}', flush=True)

    print('Building Discovery records...', flush=True)
    records = build_discovery_records(limit=None, force=False)
    print(f'Discovery records: {len(records)}', flush=True)

    print('Running Autonomous Director benchmark...', flush=True)
    director_started = time.time()
    director = build_director_report(
        records,
        goal="expanded_population_benchmark",
        max_schedule_items=max_schedule_items,
        export=export,
    )
    director_elapsed = round(time.time() - director_started, 4)
    print(f'Director complete in {director_elapsed}s', flush=True)

    confidence = director.get("scientific_confidence", {}) or {}
    provenance = director.get("provenance", {}) or {}
    timeline = director.get("timeline", {}) or {}
    health = director.get("health", {}) or {}
    lifecycle = director.get("lifecycle", {}) or {}
    export_report = lifecycle.get("export", {}) or {}

    report = {
        "success": True,
        "benchmark": "expanded_population_benchmark",
        "profile_count": len(profiles),
        "discovery_record_count": len(records),
        "director_elapsed_seconds": director_elapsed,
        "total_elapsed_seconds": round(time.time() - started, 4),
        "health": health,
        "director_summary": director.get("summary", ""),
        "scientific_confidence": {
            "summary": confidence.get("summary", ""),
            "score": confidence.get("scientific_confidence"),
            "label": confidence.get("confidence_label"),
            "components": confidence.get("components", {}),
            "inputs": confidence.get("inputs", {}),
        },
        "provenance": {
            "summary": provenance.get("summary", ""),
            "graph_summary": ((provenance.get("graph", {}) or {}).get("summary", {}) or {}),
        },
        "timeline": {
            "summary": timeline.get("text_summary", ""),
            "timeline_summary": timeline.get("summary", {}),
        },
        "learning": ((lifecycle.get("cycle", {}) or {}).get("learning_update", {}) or {}),
        "prediction": ((lifecycle.get("cycle", {}) or {}).get("prediction", {}) or {}),
        "theory": ((lifecycle.get("cycle", {}) or {}).get("theory", {}) or {}),
        "export": export_report,
        "summary": build_summary(
            profile_count=len(profiles),
            record_count=len(records),
            confidence=confidence,
            health=health,
            director_elapsed=director_elapsed,
        ),
    }

    print('Writing benchmark outputs...', flush=True)
    write_outputs(report)
    print('Benchmark outputs written.', flush=True)
    return report


def build_summary(
    *,
    profile_count: int,
    record_count: int,
    confidence: dict[str, Any],
    health: dict[str, Any],
    director_elapsed: float,
) -> str:
    """Build benchmark summary."""
    return (
        f"Expanded population benchmark completed across {record_count} discovery record(s) "
        f"from {profile_count} compiled profile(s). "
        f"Director health: {'healthy' if health.get('healthy') else 'warnings'}. "
        f"Scientific confidence: {confidence.get('scientific_confidence')} "
        f"({confidence.get('confidence_label')}). "
        f"Director elapsed: {director_elapsed}s."
    )


def write_outputs(report: dict[str, Any]) -> None:
    """Write JSON and markdown outputs."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    JSON_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    MD_PATH.write_text(
        build_markdown(report),
        encoding="utf-8",
    )


def build_markdown(report: dict[str, Any]) -> str:
    """Build markdown benchmark."""
    confidence = report.get("scientific_confidence", {}) or {}
    provenance = report.get("provenance", {}) or {}
    timeline = report.get("timeline", {}) or {}
    learning = report.get("learning", {}) or {}
    prediction = report.get("prediction", {}) or {}
    theory = report.get("theory", {}) or {}
    export = report.get("export", {}) or {}

    graph_summary = provenance.get("graph_summary", {}) or {}
    timeline_summary = timeline.get("timeline_summary", {}) or {}

    lines = [
        "# Atlas Expanded Population Benchmark",
        "",
        report.get("summary", ""),
        "",
        "## Corpus",
        "",
        f"- Compiled profiles: `{report.get('profile_count')}`",
        f"- Discovery records: `{report.get('discovery_record_count')}`",
        f"- Director elapsed seconds: `{report.get('director_elapsed_seconds')}`",
        f"- Total elapsed seconds: `{report.get('total_elapsed_seconds')}`",
        "",
        "## Director",
        "",
        report.get("director_summary", ""),
        "",
        "## Scientific Confidence",
        "",
        f"- Score: `{confidence.get('score')}`",
        f"- Label: `{confidence.get('label')}`",
        f"- Summary: {confidence.get('summary')}",
        "",
        "### Confidence Components",
        "",
    ]

    for key, value in (confidence.get("components", {}) or {}).items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend([
        "",
        "## Learning",
        "",
        f"- Learning score: `{learning.get('learning_score')}`",
        f"- Learning label: `{learning.get('learning_label')}`",
        f"- Signal count: `{learning.get('signal_count')}`",
        "",
        "## Theory",
        "",
        f"- Summary: {theory.get('summary', 'n/a')}",
        f"- Promoted count: `{theory.get('promoted_count', 0)}`",
        f"- Candidate count: `{theory.get('candidate_count', 0)}`",
        "",
        "## Prediction",
        "",
        prediction.get("summary", "n/a"),
        "",
        "## Provenance",
        "",
        f"- Summary: {provenance.get('summary')}",
        f"- Nodes: `{graph_summary.get('node_count', 0)}`",
        f"- Edges: `{graph_summary.get('edge_count', 0)}`",
        "",
        "## Timeline",
        "",
        f"- Summary: {timeline.get('summary')}",
        f"- Event count: `{timeline_summary.get('event_count', 0)}`",
        f"- Event types: `{len(timeline_summary.get('event_type_counts', {}) or {})}`",
        "",
        "## Export",
        "",
        f"- Summary: {export.get('summary', 'n/a')}",
        "",
        "### Export Files",
        "",
    ])

    files = ((export.get("export", {}) or {}).get("files", {}) or {})
    if files:
        for key, value in files.items():
            lines.append(f"- `{key}`: `{value}`")
    else:
        lines.append("- No export files recorded.")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = build_expanded_population_benchmark()
    print(report["success"])
    print(report["summary"])
    print(f"JSON: {JSON_PATH}")
    print(f"Markdown: {MD_PATH}")


if __name__ == "__main__":
    main()
