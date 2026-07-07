
"""Autonomous Research Campaign report."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.campaigns.archive import save_campaign_report
from atlas.autonomous.campaigns.runner import run_research_campaign


CAMPAIGN_REPORT_VERSION = "1.0.0"


def build_research_campaign_report(
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
    archive: bool = True,
) -> dict[str, Any]:
    """Build full research campaign report."""
    report = run_research_campaign(
        records,
        campaign_id=campaign_id,
        goal=goal,
        description=description,
        max_cycles=max_cycles,
        confidence_target=confidence_target,
        max_schedule_items=max_schedule_items,
        holdout_ratio=holdout_ratio,
        export=export,
    )

    archive_result = None
    if archive:
        archive_result = save_campaign_report(report)

    return {
        "success": True,
        "version": CAMPAIGN_REPORT_VERSION,
        **report,
        "archive": archive_result,
    }
