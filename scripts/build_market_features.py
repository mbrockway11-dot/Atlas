
"""Build investment alpha market features."""

from __future__ import annotations

import argparse
from pathlib import Path

from atlas.investment.alpha.market_features import build_market_feature_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"C:\Users\lyfe1\OneDrive\Desktop\sigil-engine")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_market_feature_report(Path(args.root))

    print(report["success"])
    print(report["summary"])
    print("Asset rows:", report.get("asset_feature_rows"))
    print("Market rows:", report.get("market_feature_rows"))
    print("Assets:", report.get("assets"))


if __name__ == "__main__":
    main()
