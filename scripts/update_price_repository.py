
"""Update the segmented Atlas price repository."""

from __future__ import annotations

from atlas.investment.price_repository import (
    build_price_repository_report,
)


def main() -> None:
    report = build_price_repository_report()

    print(report["success"])
    print(report["summary"])
    print("Counts:", report.get("counts"))

    for row in report.get(
        "status_rows",
        [],
    ):
        print({
            "asset": row.get("asset"),
            "timeframe": row.get("timeframe"),
            "rows": row.get("row_count"),
            "healthy": row.get("healthy"),
            "earliest": row.get(
                "earliest_timestamp"
            ),
            "latest": row.get(
                "latest_timestamp"
            ),
        })

    print("Errors:", report.get("fetch_errors"))
    print("Outputs:", report.get("outputs"))


if __name__ == "__main__":
    main()
