
"""Update Execution Engine."""

from __future__ import annotations

import argparse

from atlas.investment.execution_engine import build_execution_engine_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="paper", choices=["paper", "live"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_execution_engine_report(mode=args.mode)

    print(report["success"])
    print(report["summary"])
    print("Batch:", report["batch"])

    for row in report.get("orders", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
