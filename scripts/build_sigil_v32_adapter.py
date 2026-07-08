
"""Build Sigil V32 adapter report."""

from __future__ import annotations

import argparse

from atlas.investment.adapters.sigil_v32 import build_sigil_v32_adapter_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"C:\Projects\sigil-engine-git")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_sigil_v32_adapter_report(root=args.root)

    print(report["success"])
    print(report["summary"])
    for row in report.get("signals", []):
        print(row)
    print("Outputs:", report.get("outputs"))


if __name__ == "__main__":
    main()
