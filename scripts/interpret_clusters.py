"""Interpret Atlas corpus clusters."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from atlas.features.cluster_interpretation import (  # noqa: E402
    cluster_interpretation_to_text,
    interpret_cluster_report,
    load_cluster_report,
)


def main() -> None:
    """Interpret cluster report."""
    parser = argparse.ArgumentParser(
        description="Interpret Atlas corpus clusters."
    )

    parser.add_argument(
        "--input",
        default="research/corpus/clusters.json",
        help="Input clusters JSON path.",
    )

    parser.add_argument(
        "--output",
        default="research/corpus/cluster_interpretation.json",
        help="Output cluster interpretation JSON path.",
    )

    args = parser.parse_args()

    report = load_cluster_report(args.input)
    interpretation = interpret_cluster_report(report)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(interpretation, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    print(cluster_interpretation_to_text(interpretation))
    print()
    print(f"Wrote cluster interpretation: {output_path}")


if __name__ == "__main__":
    main()