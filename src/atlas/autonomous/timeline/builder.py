
"""Research timeline builder."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.timeline.events import create_timeline_event


def build_timeline_from_director(director_report: dict[str, Any]) -> list[dict[str, Any]]:
    """Build timeline events from Director report."""
    events = []

    events.append(
        create_timeline_event(
            event_type="director",
            title="Director run completed",
            summary=director_report.get("summary", ""),
            source_id="director",
            payload={
                "goal": director_report.get("goal"),
                "health": director_report.get("health"),
            },
        )
    )

    lifecycle = director_report.get("lifecycle", {}) or {}
    cycle = lifecycle.get("cycle", {}) or {}

    learning = cycle.get("learning_update", {}) or {}
    if learning:
        events.append(
            create_timeline_event(
                event_type="learning",
                title="Learning update integrated",
                summary=learning.get("summary", ""),
                source_id="learning",
                payload=learning,
            )
        )

    confidence = cycle.get("scientific_confidence", {}) or {}
    if confidence:
        events.append(
            create_timeline_event(
                event_type="confidence",
                title="Scientific confidence assigned",
                summary=confidence.get("summary", ""),
                source_id="scientific_confidence",
                payload=confidence,
            )
        )

    theory = cycle.get("theory", {}) or {}
    for item in theory.get("theories", []) or []:
        title = "Theory promoted" if item.get("status") == "promoted" else "Theory candidate registered"
        events.append(
            create_timeline_event(
                event_type="theory",
                title=title,
                summary=item.get("label", item.get("theory_id", "")),
                source_id=item.get("theory_id", ""),
                payload=item,
            )
        )

    falsification = cycle.get("falsification", {}) or {}
    if falsification:
        events.append(
            create_timeline_event(
                event_type="falsification",
                title="Falsification executed",
                summary=falsification.get("summary", ""),
                source_id="falsification",
                payload=falsification,
            )
        )

    prediction = cycle.get("prediction", {}) or {}
    if prediction:
        events.append(
            create_timeline_event(
                event_type="prediction",
                title="Prediction benchmark scored",
                summary=prediction.get("summary", ""),
                source_id="prediction",
                payload=prediction,
            )
        )

    evidence_registry = cycle.get("evidence_registry", {}) or {}
    evidence_records = evidence_registry.get("records", {}) or {}
    for evidence_id, evidence in evidence_records.items():
        events.append(
            create_timeline_event(
                event_type="evidence",
                title="Evidence registered",
                summary=evidence.get("claim", evidence.get("question", evidence_id)),
                source_id=evidence_id,
                payload=evidence,
            )
        )

    provenance = cycle.get("provenance", {}) or {}
    if provenance:
        events.append(
            create_timeline_event(
                event_type="provenance",
                title="Provenance graph generated",
                summary=provenance.get("summary", ""),
                source_id="provenance",
                payload=provenance.get("graph", {}),
            )
        )

    return sort_timeline_events(events)


def build_timeline_from_campaign(campaign_report: dict[str, Any]) -> list[dict[str, Any]]:
    """Build timeline from campaign report."""
    campaign = campaign_report.get("campaign", {}) or {}
    events = []

    events.append(
        create_timeline_event(
            event_type="campaign",
            title="Campaign completed",
            summary=campaign_report.get("summary", ""),
            source_id=campaign.get("campaign_id", ""),
            payload=campaign,
        )
    )

    for cycle in campaign.get("cycles", []) or []:
        director = cycle.get("director", {}) or {}
        events.extend(build_timeline_from_director(director))

    return sort_timeline_events(events)


def sort_timeline_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort timeline events by timestamp."""
    return sorted(events, key=lambda item: item.get("timestamp", ""))
