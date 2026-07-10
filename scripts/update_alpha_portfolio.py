
"""Update Alpha Portfolio v3.1."""

from __future__ import annotations

from atlas.investment.alpha_portfolio import build_alpha_portfolio_report


def main() -> None:
    report = build_alpha_portfolio_report()

    print(report["success"])
    print(report["summary"])

    for row in report.get("rows", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
