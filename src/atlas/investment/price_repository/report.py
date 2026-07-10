
"""Price Repository v1 build report."""

from __future__ import annotations

from datetime import datetime, UTC
import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.common.io import safe_read_csv
from atlas.investment.price_repository.config import (
    load_price_repository_config,
)
from atlas.investment.price_repository.fetcher import (
    fetch_price_segment,
)
from atlas.investment.price_repository.storage import (
    merge_segment,
    read_segment,
    segment_path,
    write_manifest,
    write_segment,
)


OUT_DIR = Path(
    "output/investment_price_repository"
)
REPORT_JSON = OUT_DIR / "price_repository_report.json"
REPORT_MD = OUT_DIR / "price_repository_report.md"
STATUS_CSV = OUT_DIR / "price_repository_status.csv"


def build_price_repository_report() -> dict[str, Any]:
    config = load_price_repository_config()

    root = Path(
        config.get(
            "repository_root",
            "data/market_prices",
        )
    )

    approved = safe_read_csv(
        Path(config["approved_universe_csv"])
    )

    if (
        approved is None
        or approved.empty
        or "asset" not in approved.columns
    ):
        return failure_report(
            "No approved market universe is available."
        )

    assets = (
        approved["asset"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )

    timeframes = (
        config.get("timeframes", {}) or {}
    )

    status_rows = []
    errors = []

    for asset in assets:
        for timeframe, settings in timeframes.items():
            path = segment_path(
                root,
                asset,
                timeframe,
            )

            existing = read_segment(path)

            incoming, error = fetch_price_segment(
                asset,
                timeframe=timeframe,
                interval=str(
                    settings.get(
                        "interval",
                        timeframe,
                    )
                ),
                period=str(
                    settings.get(
                        "period",
                        "1y",
                    )
                ),
            )

            if error:
                errors.append(error)

            merged = merge_segment(
                existing,
                incoming,
            )

            if not merged.empty:
                write_segment(path, merged)

            row_count = len(merged)

            if row_count:
                earliest = merged[
                    "timestamp"
                ].min()
                latest = merged[
                    "timestamp"
                ].max()
            else:
                earliest = None
                latest = None

            minimum_rows = int(
                settings.get(
                    "minimum_rows",
                    1,
                )
            )

            healthy = (
                row_count >= minimum_rows
            )

            status_rows.append({
                "asset": asset,
                "timeframe": timeframe,
                "row_count": row_count,
                "minimum_rows": minimum_rows,
                "healthy": healthy,
                "earliest_timestamp": (
                    earliest.isoformat()
                    if earliest is not None
                    else None
                ),
                "latest_timestamp": (
                    latest.isoformat()
                    if latest is not None
                    else None
                ),
                "existing_rows": len(existing),
                "downloaded_rows": len(incoming),
                "path": str(path),
                "provider": config.get(
                    "provider",
                ),
            })

    healthy_segments = sum(
        1
        for row in status_rows
        if row["healthy"]
    )

    required_segments = len(status_rows)

    manifest = {
        "version": "price_repository_v1",
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "provider": config.get("provider"),
        "repository_root": str(root),
        "assets": assets,
        "timeframes": list(
            timeframes.keys()
        ),
        "segment_count": required_segments,
        "healthy_segment_count": (
            healthy_segments
        ),
        "segments": status_rows,
    }

    manifest_path = write_manifest(
        root,
        manifest,
    )

    success = (
        required_segments > 0
        and healthy_segments
        == required_segments
    )

    summary = (
        f"Price Repository v1 updated "
        f"{required_segments} asset-timeframe "
        f"segment(s); {healthy_segments} passed "
        f"minimum-history requirements."
    )

    report = {
        "success": success,
        "version": "price_repository_v1",
        "generated_at": manifest[
            "generated_at"
        ],
        "summary": summary,
        "text_summary": summary,
        "assets": assets,
        "timeframes": list(
            timeframes.keys()
        ),
        "counts": {
            "assets": len(assets),
            "timeframes": len(timeframes),
            "segments": required_segments,
            "healthy_segments": (
                healthy_segments
            ),
            "unhealthy_segments": (
                required_segments
                - healthy_segments
            ),
            "fetch_errors": len(errors),
        },
        "status_rows": status_rows,
        "fetch_errors": errors,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "status_csv": str(STATUS_CSV),
            "manifest": str(manifest_path),
            "repository_root": str(root),
        },
    }

    write_outputs(report)
    return report


def failure_report(reason: str) -> dict:
    report = {
        "success": False,
        "version": "price_repository_v1",
        "summary": (
            f"Price Repository v1 blocked: "
            f"{reason}"
        ),
        "text_summary": (
            f"Price Repository v1 blocked: "
            f"{reason}"
        ),
        "counts": {},
        "status_rows": [],
        "fetch_errors": [],
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "status_csv": str(STATUS_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict) -> None:
    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(
        report.get("status_rows", [])
    ).to_csv(
        STATUS_CSV,
        index=False,
    )

    REPORT_JSON.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    lines = [
        "# Price Repository v1",
        "",
        report.get("summary", ""),
        "",
        "## Segment Status",
        "",
    ]

    for row in report.get(
        "status_rows",
        [],
    ):
        lines.append(
            f"- `{row.get('asset')}` "
            f"`{row.get('timeframe')}` ? "
            f"rows={row.get('row_count')}, "
            f"healthy={row.get('healthy')}"
        )

    REPORT_MD.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
