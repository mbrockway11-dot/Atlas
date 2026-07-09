
"""Update Portfolio Lifecycle."""

from __future__ import annotations

from atlas.investment.lifecycle import build_portfolio_lifecycle_report


def main() -> None:
    report = build_portfolio_lifecycle_report()

    print(report["success"])
    print(report["summary"])
    print("Summary:", report["lifecycle_summary"])
    print("Actions:")
    for action in report.get("actions", []):
        print("-", action)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
