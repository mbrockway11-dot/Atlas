
"""Validate alpha strategies."""

from __future__ import annotations

import argparse

from atlas.investment.alpha.validation import build_alpha_validation_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-n", type=int, default=25)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_alpha_validation_report(top_n=args.top_n)

    print(report["success"])
    print(report["summary"])
    print("Validated:", report.get("validated_count"))
    print("Promoted:", report.get("promotion", {}).get("promoted_count"))
    print("Rejected:", report.get("promotion", {}).get("rejected_count"))


if __name__ == "__main__":
    main()
