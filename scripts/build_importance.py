"""Build Atlas ablation-derived feature importance report."""

from __future__ import annotations

import argparse

from atlas.importance import (
    build_importance_from_global_ablation,
    export_importance_report,
    load_global_ablation_report,
)
from atlas.importance.ablation_importance import render_importance_report_text


def main() -> None:
    """Build feature importance report."""
    parser = argparse.ArgumentParser(
        description="Build feature importance from global ablation report."
    )

    parser.add_argument(
        "--input",
        default="research/corpus/global_ablation_report.json",
        help="Input global ablation report JSON.",
    )

    parser.add_argument(
        "--output-dir",
        default="research/corpus",
        help="Output directory.",
    )

    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of rows to print.",
    )

    args = parser.parse_args()

    report = load_global_ablation_report(args.input)
    rows = build_importance_from_global_ablation(report)
    exports = export_importance_report(rows, args.output_dir)

    print("")
    print(render_importance_report_text(rows, top_n=args.top))
    print("")
    print(f"CSV: {exports['csv']}")
    print(f"JSON: {exports['json']}")


if __name__ == "__main__":
    main()