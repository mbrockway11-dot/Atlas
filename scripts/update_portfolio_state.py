
"""Update Portfolio State."""

from __future__ import annotations

from atlas.investment.portfolio_state import build_portfolio_state_report


def main() -> None:
    report = build_portfolio_state_report()

    print(report["success"])
    print(report["summary"])
    print("Equity:", report["state"].get("equity"))
    print("Exposure:", report["state"].get("exposure"))
    print("Counts:", report["state"].get("counts"))
    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
