
"""Generate alpha hypotheses."""

from __future__ import annotations

import argparse

from atlas.investment.alpha.hypothesis import build_alpha_hypothesis_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-per-family", type=int, default=25)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_alpha_hypothesis_report(max_per_family=args.max_per_family)

    print(report["success"])
    print(report.get("summary", report.get("error", "")))
    print("Families:", report.get("families"))
    print("JSON:", report.get("json_path"))
    print("Markdown:", report.get("markdown_path"))


if __name__ == "__main__":
    main()
