
"""Price Repository health context."""

from __future__ import annotations


def build_repository_context(
    report: dict,
) -> dict:
    counts = (
        report.get("counts", {}) or {}
    )

    segments = int(
        counts.get("segments", 0) or 0
    )
    healthy = int(
        counts.get(
            "healthy_segments",
            0,
        ) or 0
    )

    coverage = (
        healthy / segments
        if segments
        else 0.0
    )

    if coverage >= 0.95:
        label = "EXCELLENT"
    elif coverage >= 0.80:
        label = "GOOD"
    elif coverage >= 0.60:
        label = "PARTIAL"
    else:
        label = "INSUFFICIENT"

    unhealthy = [
        {
            "asset": row.get("asset"),
            "timeframe": row.get(
                "timeframe"
            ),
            "rows": row.get("row_count"),
            "minimum_rows": row.get(
                "minimum_rows"
            ),
        }
        for row in report.get(
            "status_rows",
            [],
        )
        if row.get("healthy") is not True
    ]

    return {
        "coverage_ratio": round(
            coverage,
            6,
        ),
        "coverage_label": label,
        "segment_count": segments,
        "healthy_segment_count": healthy,
        "unhealthy_segments": unhealthy,
        "provider": report.get(
            "provider",
            "yfinance",
        ),
    }
