"""Atlas Discovery Engine service.

Generates corpus-level research discoveries from existing Atlas services.

Purpose:
- Detect recurring gaps.
- Detect likely high-value follow-up targets.
- Surface anomaly candidates.
- Generate research questions.
- Rank discovery opportunities.

This service is deterministic and research-oriented.
"""

from __future__ import annotations

import json
from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.services.experiment_planner_service import build_experiment_plan_payload
from atlas.services.profile_report_service import build_profile_report_payload
from atlas.services.graph_intelligence_service import build_profile_graph_intelligence_payload
from atlas.services.vedic_behavior_service import build_vedic_behavior_payload


DISCOVERY_ENGINE_VERSION = "1.0"


DEFAULT_DISCOVERY_LIMIT = 25


def list_discovery_profiles() -> list[str]:
    """Return profiles available for discovery workflows."""
    return list_saved_profiles()


def build_discovery_payload(
    *,
    limit: int = DEFAULT_DISCOVERY_LIMIT,
) -> dict[str, Any]:
    """Build corpus discovery payload."""
    profiles = list_discovery_profiles()[:limit]

    profile_summaries = []

    for profile_key in profiles:
        profile_summaries.append(build_profile_discovery_summary(profile_key))

    discoveries = build_discoveries(profile_summaries)
    gaps = build_population_gaps(profile_summaries)
    questions = build_research_questions(discoveries, gaps)
    priorities = build_discovery_priorities(discoveries, gaps)

    model = {
        "version": DISCOVERY_ENGINE_VERSION,
        "profile_count": len(profile_summaries),
        "profiles": profile_summaries,
        "discoveries": discoveries,
        "population_gaps": gaps,
        "research_questions": questions,
        "research_priorities": priorities,
        "summary": {
            "discovery_count": len(discoveries),
            "gap_count": len(gaps),
            "question_count": len(questions),
            "priority_count": len(priorities),
            "highest_priority": priorities[0] if priorities else {},
        },
    }

    return {
        "success": True,
        "version": DISCOVERY_ENGINE_VERSION,
        "errors": [],
        "warnings": build_discovery_warnings(profile_summaries),
        "data": {
            "discovery_model": model,
        },
        "exports": {
            "discovery_json": model,
            "markdown": render_discovery_markdown(model),
        },
        "metrics": build_discovery_metrics(model),
    }


def build_profile_discovery_summary(profile_key: str) -> dict[str, Any]:
    """Build compact discovery summary for one profile."""
    profile_payload = safe_service_call(
        "profile_report",
        lambda: build_profile_report_payload(profile_key),
    )

    graph_payload = safe_service_call(
        "graph_intelligence",
        lambda: build_profile_graph_intelligence_payload(profile_key),
    )

    vedic_payload = safe_service_call(
        "vedic_behavior",
        lambda: build_vedic_behavior_payload(profile_key),
    )

    experiment_query = f"Explain {profile_key.replace('_', ' ')}"
    experiment_payload = safe_service_call(
        "experiment_planner",
        lambda: build_experiment_plan_payload(experiment_query),
    )

    return {
        "profile_key": profile_key,
        "profile_report": compact_service_summary(profile_payload),
        "graph_intelligence": compact_service_summary(graph_payload),
        "vedic_behavior": compact_service_summary(vedic_payload),
        "experiment_plan": compact_service_summary(experiment_payload),
        "signals": build_profile_signals(
            profile_payload=profile_payload,
            graph_payload=graph_payload,
            vedic_payload=vedic_payload,
            experiment_payload=experiment_payload,
        ),
    }


def build_profile_signals(
    *,
    profile_payload: dict[str, Any],
    graph_payload: dict[str, Any],
    vedic_payload: dict[str, Any],
    experiment_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build discovery signals from service summaries."""
    profile_metrics = profile_payload.get("metrics", {})
    graph_metrics = graph_payload.get("metrics", {})
    vedic_metrics = vedic_payload.get("metrics", {})
    experiment_metrics = experiment_payload.get("metrics", {})

    missing_artifacts = profile_metrics.get("missing_artifacts", [])

    return {
        "has_temporal": bool(profile_metrics.get("has_temporal")),
        "has_graph": bool(profile_metrics.get("has_graph")),
        "missing_artifact_count": len(missing_artifacts),
        "missing_artifacts": missing_artifacts,
        "profile_warning_count": len(profile_payload.get("warnings", [])),
        "graph_confidence": graph_metrics.get("overall_confidence", {}),
        "vedic_confidence": vedic_metrics.get("overall_confidence", {}),
        "vedic_assumption_count": vedic_metrics.get("assumption_count", 0),
        "moon_nakshatra": vedic_metrics.get("moon_nakshatra", ""),
        "dasha_periods": vedic_metrics.get("dasha_periods", 0),
        "recommended_experiment": experiment_metrics.get("recommended_next_experiment"),
        "highest_value_score": experiment_metrics.get("highest_value_score", {}),
        "average_expected_gain": experiment_metrics.get("average_expected_gain", 0),
        "average_effort": experiment_metrics.get("average_effort", 0),
    }


def build_discoveries(profile_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build discovery records."""
    discoveries = []

    discoveries.extend(discover_temporal_bottlenecks(profile_summaries))
    discoveries.extend(discover_graph_confidence_patterns(profile_summaries))
    discoveries.extend(discover_overlay_limitations(profile_summaries))
    discoveries.extend(discover_high_value_experiments(profile_summaries))

    return rank_discoveries(discoveries)


def discover_temporal_bottlenecks(
    profile_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Discover recurring temporal bottlenecks."""
    affected = [
        profile
        for profile in profile_summaries
        if not profile.get("signals", {}).get("moon_nakshatra")
    ]

    if not affected:
        return []

    return [
        discovery(
            title="Recurring Moon Nakshatra Resolution Gap",
            discovery_type="population_gap",
            summary=(
                "Multiple profiles have unresolved Moon Nakshatra values, which limits "
                "temporal, dasha, behavioral-assumption, and reasoning confidence."
            ),
            confidence=confidence_from_ratio(len(affected), len(profile_summaries)),
            novelty=confidence_record(0.70),
            supporting_profiles=[profile.get("profile_key") for profile in affected],
            evidence=[
                f"Affected profiles: {len(affected)}",
                f"Total profiles inspected: {len(profile_summaries)}",
            ],
            recommended_followup=[
                "Prioritize Moon Nakshatra resolution across the corpus.",
                "Rerun temporal intelligence after repair.",
                "Compare confidence before and after temporal repair.",
            ],
        )
    ]


def discover_graph_confidence_patterns(
    profile_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Discover graph confidence patterns."""
    limited = []

    for profile in profile_summaries:
        graph_confidence = profile.get("signals", {}).get("graph_confidence", {})
        if graph_confidence.get("label") in {"limited", "low"}:
            limited.append(profile)

    if not limited:
        return []

    return [
        discovery(
            title="Graph Intelligence Confidence Bottleneck",
            discovery_type="graph_gap",
            summary=(
                "A subset of inspected profiles has limited or low graph intelligence confidence. "
                "These profiles may need graph enrichment before topology-heavy conclusions."
            ),
            confidence=confidence_from_ratio(len(limited), len(profile_summaries)),
            novelty=confidence_record(0.65),
            supporting_profiles=[profile.get("profile_key") for profile in limited],
            evidence=[
                f"Limited/low graph profiles: {len(limited)}",
                f"Total profiles inspected: {len(profile_summaries)}",
            ],
            recommended_followup=[
                "Inspect CIG/STG node and edge counts.",
                "Rebuild or enrich graph artifacts for limited-confidence profiles.",
                "Compare graph confidence before and after repair.",
            ],
        )
    ]


def discover_overlay_limitations(
    profile_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Discover Vedic overlay limitation patterns."""
    limited = []

    for profile in profile_summaries:
        vedic_confidence = profile.get("signals", {}).get("vedic_confidence", {})
        if vedic_confidence.get("label") in {"limited", "low"}:
            limited.append(profile)

    if not limited:
        return []

    return [
        discovery(
            title="Vedic Behavior Overlay Limited by Source Completeness",
            discovery_type="overlay_gap",
            summary=(
                "The optional Vedic behavior layer frequently produces limited-confidence "
                "assumptions, usually because timing-sensitive temporal inputs are incomplete."
            ),
            confidence=confidence_from_ratio(len(limited), len(profile_summaries)),
            novelty=confidence_record(0.60),
            supporting_profiles=[profile.get("profile_key") for profile in limited],
            evidence=[
                f"Limited/low Vedic overlay profiles: {len(limited)}",
                f"Total profiles inspected: {len(profile_summaries)}",
            ],
            recommended_followup=[
                "Keep Vedic Behavior as an optional overlay, not a default Atlas AI core service.",
                "Resolve Moon Nakshatra and birth-time inputs before strong behavioral interpretation.",
                "Use behavioral assumptions only as hypothesis-level context.",
            ],
        )
    ]


def discover_high_value_experiments(
    profile_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Discover recurring high-value experiments."""
    temporal_repairs = []

    for profile in profile_summaries:
        experiment = profile.get("signals", {}).get("recommended_experiment") or ""
        if "Temporal Repair" in experiment:
            temporal_repairs.append(profile)

    if not temporal_repairs:
        return []

    return [
        discovery(
            title="Temporal Repair Is the Dominant Recommended Experiment",
            discovery_type="experiment_pattern",
            summary=(
                "Experiment Planner repeatedly recommends temporal repair as the next best action. "
                "This indicates temporal completeness is currently one of the highest-value corpus repairs."
            ),
            confidence=confidence_from_ratio(len(temporal_repairs), len(profile_summaries)),
            novelty=confidence_record(0.75),
            supporting_profiles=[profile.get("profile_key") for profile in temporal_repairs],
            evidence=[
                f"Temporal repair recommended for: {len(temporal_repairs)} profiles",
                f"Total profiles inspected: {len(profile_summaries)}",
            ],
            recommended_followup=[
                "Create a temporal repair batch script.",
                "Prioritize profiles where temporal repair has the highest expected gain.",
                "Track confidence gain after repair.",
            ],
        )
    ]


def build_population_gaps(profile_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build population gap records."""
    gaps = []

    gaps.append(
        gap_record(
            name="Missing research session artifacts",
            affected=[
                profile
                for profile in profile_summaries
                if "research_session.json"
                in profile.get("signals", {}).get("missing_artifacts", [])
            ],
            total=len(profile_summaries),
            repair="Generate or restore research_session.json for affected profiles.",
        )
    )

    gaps.append(
        gap_record(
            name="Unresolved Moon Nakshatra",
            affected=[
                profile
                for profile in profile_summaries
                if not profile.get("signals", {}).get("moon_nakshatra")
            ],
            total=len(profile_summaries),
            repair="Repair Moon Nakshatra resolution in temporal intelligence.",
        )
    )

    gaps.append(
        gap_record(
            name="Limited Vedic overlay confidence",
            affected=[
                profile
                for profile in profile_summaries
                if profile.get("signals", {})
                .get("vedic_confidence", {})
                .get("label")
                in {"limited", "low"}
            ],
            total=len(profile_summaries),
            repair="Improve temporal inputs before using behavioral assumptions.",
        )
    )

    return [gap for gap in gaps if gap.get("affected_count", 0) > 0]


def gap_record(
    *,
    name: str,
    affected: list[dict[str, Any]],
    total: int,
    repair: str,
) -> dict[str, Any]:
    """Build population gap record."""
    ratio = len(affected) / total if total else 0.0

    return {
        "name": name,
        "affected_count": len(affected),
        "total_count": total,
        "affected_ratio": round(ratio, 4),
        "confidence": confidence_record(ratio),
        "affected_profiles": [profile.get("profile_key") for profile in affected],
        "recommended_repair": repair,
    }


def build_research_questions(
    discoveries: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build research questions from discoveries and gaps."""
    questions = []

    for item in discoveries:
        questions.append(
            {
                "question": f"What changes if we repair: {item.get('title')}?",
                "source": item.get("title"),
                "priority": item.get("confidence", {}),
            }
        )

    for gap in gaps:
        questions.append(
            {
                "question": f"How much confidence is lost due to {gap.get('name')}?",
                "source": gap.get("name"),
                "priority": gap.get("confidence", {}),
            }
        )

    return questions


def build_discovery_priorities(
    discoveries: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build ranked discovery priorities."""
    priorities = []

    for item in discoveries:
        priorities.append(
            {
                "title": item.get("title"),
                "priority_type": "discovery",
                "score": item.get("confidence", {}).get("score", 0),
                "confidence": item.get("confidence", {}),
                "recommended_followup": item.get("recommended_followup", []),
            }
        )

    for gap in gaps:
        priorities.append(
            {
                "title": gap.get("name"),
                "priority_type": "gap",
                "score": gap.get("confidence", {}).get("score", 0),
                "confidence": gap.get("confidence", {}),
                "recommended_followup": [gap.get("recommended_repair")],
            }
        )

    return sorted(
        priorities,
        key=lambda item: safe_float(item.get("score")),
        reverse=True,
    )


def discovery(
    *,
    title: str,
    discovery_type: str,
    summary: str,
    confidence: dict[str, Any],
    novelty: dict[str, Any],
    supporting_profiles: list[str],
    evidence: list[str],
    recommended_followup: list[str],
) -> dict[str, Any]:
    """Build discovery record."""
    return {
        "title": title,
        "discovery_type": discovery_type,
        "summary": summary,
        "confidence": confidence,
        "novelty": novelty,
        "supporting_profiles": supporting_profiles,
        "evidence": evidence,
        "recommended_followup": recommended_followup,
        "profile_count": len(supporting_profiles),
    }


def rank_discoveries(discoveries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank discoveries by confidence and novelty."""
    return sorted(
        discoveries,
        key=lambda item: (
            safe_float(item.get("confidence", {}).get("score")) * 0.7
            + safe_float(item.get("novelty", {}).get("score")) * 0.3
        ),
        reverse=True,
    )


def safe_service_call(name: str, fn) -> dict[str, Any]:
    """Safely call a discovery source service."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "errors": [f"{name} failed: {exc}"],
            "warnings": [],
            "data": {},
            "exports": {},
            "metrics": {},
        }


def compact_service_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Compact service payload for discovery."""
    return {
        "success": payload.get("success", False),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
    }


def build_discovery_warnings(profile_summaries: list[dict[str, Any]]) -> list[str]:
    """Build discovery warnings."""
    warnings = []

    failed_profiles = [
        profile.get("profile_key")
        for profile in profile_summaries
        if not profile.get("profile_report", {}).get("success")
    ]

    if failed_profiles:
        warnings.append(f"Profile report failed for {len(failed_profiles)} profiles.")

    return warnings


def build_discovery_metrics(model: dict[str, Any]) -> dict[str, Any]:
    """Build discovery metrics."""
    markdown = render_discovery_markdown(model)

    return {
        "profile_count": model.get("profile_count", 0),
        "discovery_count": len(model.get("discoveries", [])),
        "gap_count": len(model.get("population_gaps", [])),
        "question_count": len(model.get("research_questions", [])),
        "priority_count": len(model.get("research_priorities", [])),
        "word_count": len(markdown.split()),
        "highest_priority": model.get("summary", {}).get("highest_priority", {}),
    }


def render_discovery_markdown(model: dict[str, Any]) -> str:
    """Render discovery model as Markdown."""
    lines = [
        "# Atlas Discovery Engine",
        "",
        f"**Version:** {model.get('version', DISCOVERY_ENGINE_VERSION)}",
        f"**Profiles inspected:** {model.get('profile_count', 0)}",
        "",
        "## Top Research Priority",
    ]

    highest = model.get("summary", {}).get("highest_priority", {})
    if highest:
        lines.append(f"**{highest.get('title', 'Untitled')}**")
        lines.append(f"Type: {highest.get('priority_type', 'unknown')}")
        confidence = highest.get("confidence", {})
        lines.append(
            f"Confidence: {confidence.get('percent', 0)}% "
            f"{confidence.get('label', 'unknown')}"
        )

    lines.append("")
    lines.append("## Discoveries")

    for item in model.get("discoveries", []):
        confidence = item.get("confidence", {})
        novelty = item.get("novelty", {})

        lines.append(f"### {item.get('title', 'Untitled')}")
        lines.append(item.get("summary", ""))
        lines.append(
            f"Confidence: {confidence.get('percent', 0)}% "
            f"{confidence.get('label', 'unknown')}"
        )
        lines.append(
            f"Novelty: {novelty.get('percent', 0)}% "
            f"{novelty.get('label', 'unknown')}"
        )

        lines.append("")
        lines.append("Evidence:")
        for evidence in item.get("evidence", []):
            lines.append(f"- {evidence}")

        lines.append("")
        lines.append("Follow-up:")
        for followup in item.get("recommended_followup", []):
            lines.append(f"- {followup}")

        lines.append("")

    lines.append("## Population Gaps")

    for gap in model.get("population_gaps", []):
        confidence = gap.get("confidence", {})
        lines.append(f"### {gap.get('name')}")
        lines.append(
            f"Affected: {gap.get('affected_count')} / {gap.get('total_count')}"
        )
        lines.append(
            f"Confidence: {confidence.get('percent', 0)}% "
            f"{confidence.get('label', 'unknown')}"
        )
        lines.append(f"Recommended repair: {gap.get('recommended_repair')}")
        lines.append("")

    lines.append("## Research Questions")

    for question in model.get("research_questions", []):
        lines.append(f"- {question.get('question')}")

    return "\n".join(lines).strip() + "\n"


def confidence_from_ratio(count: int, total: int) -> dict[str, Any]:
    """Build confidence from ratio."""
    ratio = count / total if total else 0.0
    return confidence_record(ratio)


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
    if score >= 0.85:
        return "high"
    if score >= 0.65:
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


def clamp(value: float) -> float:
    """Clamp score to 0..1."""
    return max(0.0, min(1.0, value))


def json_export(data: Any) -> str:
    """Serialize discovery JSON."""
    return json.dumps(data, indent=2, sort_keys=True)