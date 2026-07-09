
"""Atlas Core report export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


OUT_DIR = Path("output/atlas_core")
REPORT_JSON = OUT_DIR / "atlas_core_report.json"
REPORT_MD = OUT_DIR / "atlas_core_report.md"


def write_core_report(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Atlas Core Report",
        "",
        f"- Success: `{report.get('success')}`",
        f"- Run ID: `{report.get('run_id')}`",
        f"- Mode: `{report.get('mode')}`",
        f"- Nodes executed: `{report.get('node_count')}`",
        "",
        "## Nodes",
        "",
    ]

    for row in report.get("results", []):
        lines.append(
            f"- `{row.get('name')}` success=`{row.get('success')}` output=`{row.get('output_key')}`"
        )

    return "\n".join(lines) + "\n"
