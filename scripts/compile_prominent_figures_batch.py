
"""Compile prominent figures using Atlas Population Compiler."""

from __future__ import annotations

import argparse

from atlas.population.compiler import build_population_compile_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    report = build_population_compile_report(
        limit=args.limit,
        force=args.force,
    )

    print(report["summary"])
    print(f"Tracked compiled: {report['tracked_compiled']}")
    print(f"Tracked failed: {report['tracked_failed']}")
    print(f"Report: {report['report_path']}")


if __name__ == "__main__":
    main()
