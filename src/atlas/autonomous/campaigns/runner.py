
"""Autonomous Research Campaign runner."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.campaigns.models import create_campaign
from atlas.autonomous.campaigns.scoring import campaign_label, score_campaign_confidence
from atlas.autonomous.campaigns.state import add_campaign_cycle, transition_campaign
from atlas.autonomous.director import build_director_report


def run_research_campaign(
    records: list[dict[str, Any]],
    *,
    campaign_id: str,
    goal: str,
    description: str = "",
    max_cycles: int = 3,
    confidence_target: float = 0.80,
    max_schedule_items: int = 5,
    holdout_ratio: float = 0.20,
    export: bool = True,
) -> dict[str, Any]:
    """Run autonomous research campaign."""
    campaign = create_campaign(
        campaign_id=campaign_id,
        goal=goal,
        description=description,
        max_cycles=max_cycles,
        confidence_target=confidence_target,
    )

    campaign = transition_campaign(campaign, "running", note="Campaign started.")

    for cycle_index in range(1, max_cycles + 1):
        director_report = build_director_report(
            records,
            goal=goal,
            max_schedule_items=max_schedule_items,
            holdout_ratio=holdout_ratio,
            export=export,
        )

        campaign = add_campaign_cycle(campaign, director_report)
        confidence = score_campaign_confidence(campaign)
        campaign["current_confidence"] = confidence
        campaign["confidence_label"] = campaign_label(confidence)

        if confidence >= confidence_target:
            campaign = transition_campaign(
                campaign,
                "target_reached",
                note=f"Confidence target reached on cycle {cycle_index}.",
            )
            break

    if campaign.get("status") == "running":
        campaign = transition_campaign(
            campaign,
            "completed",
            note="Campaign completed max cycles.",
        )

    campaign["summary"] = build_campaign_summary(campaign)

    return {
        "success": True,
        "campaign": campaign,
        "summary": campaign["summary"],
    }


def build_campaign_summary(campaign: dict[str, Any]) -> str:
    """Build campaign summary."""
    return (
        f"Research campaign '{campaign.get('campaign_id')}' completed with status "
        f"{campaign.get('status')} after {len(campaign.get('cycles', []) or [])} cycle(s). "
        f"Confidence: {campaign.get('current_confidence')} "
        f"({campaign.get('confidence_label')})."
    )
