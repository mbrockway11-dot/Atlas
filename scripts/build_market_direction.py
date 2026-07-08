
"""Build Market Direction Engine report."""

from __future__ import annotations

from atlas.investment.direction import build_market_direction_report


def main() -> None:
    report = build_market_direction_report()

    print(report["success"])
    print(report["summary"])
    print("Vote:", report["vote"])
    print("Exposure:", report["exposure"])
    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
