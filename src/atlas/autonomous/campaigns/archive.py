
"""Campaign archive writer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CAMPAIGN_DIR = Path("output/campaigns")


def save_campaign_report(
    campaign_report: dict[str, Any],
    *,
    output_dir: str | Path = DEFAULT_CAMPAIGN_DIR,
) -> dict[str, Any]:
    """Save campaign report."""
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    campaign = campaign_report.get("campaign", {}) or {}
    campaign_id = campaign.get("campaign_id", "campaign")

    json_path = target / f"{campaign_id}.json"
    md_path = target / f"{campaign_id}.md"

    json_path.write_text(
        json.dumps(campaign_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    md_path.write_text(
        build_campaign_markdown(campaign_report),
        encoding="utf-8",
    )

    return {
        "success": True,
        "files": {
            "json": str(json_path),
            "markdown": str(md_path),
        },
    }


def build_campaign_markdown(campaign_report: dict[str, Any]) -> str:
    """Build campaign markdown."""
    campaign = campaign_report.get("campaign", {}) or {}

    lines = [
        f"# Atlas Research Campaign: {campaign.get('campaign_id')}",
        "",
        "## Summary",
        "",
        campaign_report.get("summary", ""),
        "",
        "## Goal",
        "",
        campaign.get("goal", ""),
        "",
        "## Status",
        "",
        f"- Status: `{campaign.get('status')}`",
        f"- Current confidence: `{campaign.get('current_confidence')}`",
        f"- Confidence label: `{campaign.get('confidence_label')}`",
        f"- Cycles: `{len(campaign.get('cycles', []) or [])}`",
        "",
        "## Cycles",
        "",
    ]

    for cycle in campaign.get("cycles", []) or []:
        lines.extend([
            f"### Cycle {cycle.get('cycle_index')}",
            "",
            cycle.get("summary", ""),
            "",
            f"- Learning: `{(cycle.get('learning_update', {}) or {}).get('learning_label')}`",
            f"- Learning score: `{(cycle.get('learning_update', {}) or {}).get('learning_score')}`",
            f"- Theory summary: {(cycle.get('theory', {}) or {}).get('summary')}",
            f"- Prediction summary: {(cycle.get('prediction', {}) or {}).get('summary')}",
            "",
        ])

    return "\n".join(lines).strip() + "\n"
