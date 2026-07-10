
"""Update Atlas Market Universe v1."""

from __future__ import annotations

from atlas.investment.market_universe import (
    build_market_universe_report,
)


def main() -> None:
    report = build_market_universe_report()

    print(report["success"])
    print(report["summary"])
    print("Approved:", report["approved_assets"])
    print("Rejected:", report["rejected_assets"])

    print("Status:")
    for row in report.get("status_rows", []):
        print({
            "asset": row.get("asset"),
            "status": row.get("status"),
            "observations": row.get("observation_count"),
            "median_dollar_volume": row.get(
                "median_daily_dollar_volume"
            ),
            "stale_days": row.get("stale_days"),
            "failure_reasons": row.get("failure_reasons"),
        })

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
