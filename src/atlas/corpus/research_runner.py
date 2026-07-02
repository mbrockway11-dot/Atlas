"""Atlas corpus research runner.

Runs the Atlas Research Cycle across multiple corpus profiles.

This module does not build profiles.
It assumes profiles already exist in the Atlas profile library/corpus and runs
scientific research cycles across selected profile keys.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.research.research_cycle import build_research_cycle_payload


CORPUS_RESEARCH_RUNNER_VERSION = "1.0"

OUTPUT_DIR = Path("output") / "corpus_research"
INDEX_PATH = OUTPUT_DIR / "corpus_research_index.json"


def run_corpus_research(
    *,
    limit: int | None = None,
    profile_keys: list[str] | None = None,
    include_memory: bool = False,
    include_validation: bool = True,
    validation_domains: list[str] | None = None,
) -> dict[str, Any]:
    """Run research cycles across corpus profiles."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    selected_profiles = select_profiles(
        profile_keys=profile_keys,
        limit=limit,
    )

    results: list[dict[str, Any]] = []

    for profile_key in selected_profiles:
        query = f"Explain {profile_key}"
        payload = safe_call(
            profile_key,
            lambda key=profile_key, q=query: build_research_cycle_payload(
                q,
                include_memory=include_memory,
                include_validation=include_validation,
                validation_domains=validation_domains,
            ),
        )

        result = build_profile_research_result(
            profile_key=profile_key,
            query=query,
            payload=payload,
        )
        results.append(result)

        write_profile_result(result)

    run_model = build_corpus_research_model(
        results=results,
        include_memory=include_memory,
        include_validation=include_validation,
        validation_domains=validation_domains,
    )

    write_run_index(run_model)

    return {
        "success": run_model.get("failed_profiles", 0) == 0,
        "version": CORPUS_RESEARCH_RUNNER_VERSION,
        "errors": collect_run_errors(results),
        "warnings": collect_run_warnings(results),
        "data": {
            "corpus_research": run_model,
        },
        "exports": {
            "corpus_research_json": run_model,
            "markdown": render_corpus_research_markdown(run_model),
        },
        "metrics": build_corpus_research_metrics(run_model),
    }


def select_profiles(
    *,
    profile_keys: list[str] | None,
    limit: int | None,
) -> list[str]:
    """Select profiles for corpus research."""
    if profile_keys:
        selected = profile_keys
    else:
        selected = list_saved_profiles()

    if limit is not None:
        return selected[: max(0, limit)]

    return selected


def build_profile_research_result(
    *,
    profile_key: str,
    query: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build one compact profile research result."""
    cycle = payload.get("data", {}).get("research_cycle", {})
    summary = cycle.get("cycle_summary", {})
    metrics = payload.get("metrics", {})
    confidence = metrics.get("overall_confidence", {})

    return {
        "profile_key": profile_key,
        "query": query,
        "success": payload.get("success", False),
        "state": metrics.get("state"),
        "intent": metrics.get("intent"),
        "scope": metrics.get("scope"),
        "validation_profile_count": metrics.get("validation_profile_count", 0),
        "memory_recorded": metrics.get("memory_recorded", False),
        "next_question_count": metrics.get("next_question_count", 0),
        "overall_confidence": confidence,
        "best_hypothesis": summary.get("best_hypothesis"),
        "highest_falsification_case": summary.get("highest_falsification_case"),
        "recommended_experiment": summary.get("recommended_experiment"),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "path": str(profile_result_path(profile_key)),
    }


def build_corpus_research_model(
    *,
    results: list[dict[str, Any]],
    include_memory: bool,
    include_validation: bool,
    validation_domains: list[str] | None,
) -> dict[str, Any]:
    """Build corpus research model."""
    successful = [item for item in results if item.get("success")]
    failed = [item for item in results if not item.get("success")]

    confidence_scores = [
        safe_float(item.get("overall_confidence", {}).get("score"))
        for item in successful
        if "score" in item.get("overall_confidence", {})
    ]

    average_confidence = (
        sum(confidence_scores) / len(confidence_scores)
        if confidence_scores
        else 0.0
    )

    experiment_counts = count_values(
        item.get("recommended_experiment")
        for item in results
        if item.get("recommended_experiment")
    )

    hypothesis_counts = count_values(
        item.get("best_hypothesis")
        for item in results
        if item.get("best_hypothesis")
    )

    falsification_counts = count_values(
        item.get("highest_falsification_case")
        for item in results
        if item.get("highest_falsification_case")
    )

    return {
        "version": CORPUS_RESEARCH_RUNNER_VERSION,
        "timestamp": now_iso(),
        "profile_count": len(results),
        "successful_profiles": len(successful),
        "failed_profiles": len(failed),
        "include_memory": include_memory,
        "include_validation": include_validation,
        "validation_domains": validation_domains,
        "average_confidence": confidence_record(average_confidence),
        "total_next_questions": sum(
            safe_int(item.get("next_question_count"))
            for item in results
        ),
        "memory_recorded_count": sum(
            1 for item in results if item.get("memory_recorded")
        ),
        "validation_profile_count": sum(
            safe_int(item.get("validation_profile_count"))
            for item in results
        ),
        "top_recommended_experiments": top_counts(experiment_counts),
        "top_best_hypotheses": top_counts(hypothesis_counts),
        "top_falsification_cases": top_counts(falsification_counts),
        "results": results,
        "index_path": str(INDEX_PATH),
    }


def write_profile_result(result: dict[str, Any]) -> None:
    """Write one profile research result."""
    path = profile_result_path(result.get("profile_key", "unknown"))
    path.write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def write_run_index(model: dict[str, Any]) -> None:
    """Write corpus research index."""
    INDEX_PATH.write_text(
        json.dumps(model, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def profile_result_path(profile_key: str) -> Path:
    """Return profile research result path."""
    safe_key = slugify(profile_key)
    return OUTPUT_DIR / f"{safe_key}.json"


def build_corpus_research_metrics(model: dict[str, Any]) -> dict[str, Any]:
    """Build metrics for corpus research."""
    markdown = render_corpus_research_markdown(model)

    return {
        "profile_count": model.get("profile_count", 0),
        "successful_profiles": model.get("successful_profiles", 0),
        "failed_profiles": model.get("failed_profiles", 0),
        "average_confidence": model.get("average_confidence", {}),
        "total_next_questions": model.get("total_next_questions", 0),
        "memory_recorded_count": model.get("memory_recorded_count", 0),
        "validation_profile_count": model.get("validation_profile_count", 0),
        "top_experiment_count": len(model.get("top_recommended_experiments", [])),
        "top_hypothesis_count": len(model.get("top_best_hypotheses", [])),
        "top_falsification_count": len(model.get("top_falsification_cases", [])),
        "word_count": len(markdown.split()),
    }


def render_corpus_research_markdown(model: dict[str, Any]) -> str:
    """Render corpus research model as Markdown."""
    confidence = model.get("average_confidence", {})

    lines = [
        "# Atlas Corpus Research Run",
        "",
        f"**Version:** {model.get('version', CORPUS_RESEARCH_RUNNER_VERSION)}",
        f"**Timestamp:** {model.get('timestamp', '')}",
        "",
        "## Summary",
        f"- Profiles: {model.get('profile_count', 0)}",
        f"- Successful profiles: {model.get('successful_profiles', 0)}",
        f"- Failed profiles: {model.get('failed_profiles', 0)}",
        (
            f"- Average confidence: {confidence.get('percent', 0)}% "
            f"{confidence.get('label', 'unknown')}"
        ),
        f"- Total next questions: {model.get('total_next_questions', 0)}",
        f"- Validation profile count: {model.get('validation_profile_count', 0)}",
        f"- Memory recorded count: {model.get('memory_recorded_count', 0)}",
        "",
        "## Top Recommended Experiments",
    ]

    for item in model.get("top_recommended_experiments", []):
        lines.append(f"- {item.get('value')}: {item.get('count')}")

    lines.append("")
    lines.append("## Top Hypotheses")

    for item in model.get("top_best_hypotheses", []):
        lines.append(f"- {item.get('value')}: {item.get('count')}")

    lines.append("")
    lines.append("## Top Falsification Cases")

    for item in model.get("top_falsification_cases", []):
        lines.append(f"- {item.get('value')}: {item.get('count')}")

    return "\n".join(lines).strip() + "\n"


def collect_run_errors(results: list[dict[str, Any]]) -> list[Any]:
    """Collect run errors."""
    errors = []

    for result in results:
        for error in result.get("errors", []):
            errors.append(
                {
                    "profile_key": result.get("profile_key"),
                    "error": error,
                }
            )

    return errors


def collect_run_warnings(results: list[dict[str, Any]]) -> list[str]:
    """Collect run warnings."""
    warnings = []

    for result in results:
        for warning in result.get("warnings", []):
            text = f"{result.get('profile_key')}: {warning}"
            if text not in warnings:
                warnings.append(text)

    return warnings


def safe_call(profile_key: str, fn) -> dict[str, Any]:
    """Safely call one profile research cycle."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "version": CORPUS_RESEARCH_RUNNER_VERSION,
            "errors": [f"{profile_key} failed: {exc}"],
            "warnings": [],
            "data": {},
            "exports": {},
            "metrics": {},
        }


def count_values(values) -> dict[str, int]:
    """Count values."""
    counts: dict[str, int] = {}

    for value in values:
        if not value:
            continue

        counts[str(value)] = counts.get(str(value), 0) + 1

    return counts


def top_counts(counts: dict[str, int], *, limit: int = 10) -> list[dict[str, Any]]:
    """Return top counts."""
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


def confidence_record(score: float) -> dict[str, Any]:
    """Build confidence record."""
    score = clamp(score)

    return {
        "score": round(score, 4),
        "percent": round(score * 100, 2),
        "label": confidence_label(score),
    }


def confidence_label(score: float) -> str:
    """Resolve confidence label."""
    if score >= 0.80:
        return "high"

    if score >= 0.60:
        return "moderate"

    if score >= 0.40:
        return "limited"

    return "low"


def safe_float(value: Any) -> float:
    """Convert value to float safely."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def safe_int(value: Any) -> int:
    """Convert value to int safely."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def clamp(value: float) -> float:
    """Clamp score to 0..1."""
    return max(0.0, min(1.0, value))


def slugify(value: str) -> str:
    """Slugify a profile key."""
    chars = []

    for char in value.lower():
        if char.isalnum():
            chars.append(char)
        elif char in {" ", "-", "_"}:
            chars.append("_")

    slug = "".join(chars)

    while "__" in slug:
        slug = slug.replace("__", "_")

    return slug.strip("_") or "unknown"


def now_iso() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def json_export(data: Any) -> str:
    """Serialize corpus research JSON."""
    return json.dumps(data, indent=2, sort_keys=True)