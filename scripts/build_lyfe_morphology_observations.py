"""Build LYFE morphology observations for Atlas research."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from atlas.investment.lyfe_bridge.morphology_observations import (
    DEFAULT_HORIZONS,
    build_from_paths,
)


def parse_horizons(value: str) -> tuple[int, ...]:
    return tuple(
        int(item.strip())
        for item in value.split(",")
        if item.strip()
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--topology",
        required=True,
    )

    parser.add_argument(
        "--market",
        required=True,
    )

    parser.add_argument(
        "--output",
        default=(
            "output/investment_lyfe_morphology/"
            "morphology_observations.csv"
        ),
    )

    parser.add_argument(
        "--horizons",
        default=",".join(
            str(value)
            for value in DEFAULT_HORIZONS
        ),
    )

    parser.add_argument(
        "--target-horizon",
        type=int,
        default=16,
    )

    args = parser.parse_args()

    horizons = parse_horizons(
        args.horizons
    )

    observations = build_from_paths(
        topology_path=args.topology,
        market_path=args.market,
        output_path=args.output,
        horizons=horizons,
        target_horizon=args.target_horizon,
    )

    summary = {
        "schema_version":
            "atlas.lyfe_morphology_observations.v1",
        "rows": int(len(observations)),
        "assets": sorted(
            observations["asset"]
            .astype(str)
            .unique()
            .tolist()
        ),
        "asset_count": int(
            observations["asset"].nunique()
        ),
        "timestamp_min": (
            observations["timestamp"]
            .min()
            .isoformat()
        ),
        "timestamp_max": (
            observations["timestamp"]
            .max()
            .isoformat()
        ),
        "rank_state_count": int(
            observations["rank_state"].nunique()
        ),
        "transition_count": int(
            observations["transition"].nunique()
        ),
        "horizons": list(horizons),
        "target_horizon": int(
            args.target_horizon
        ),
        "output": str(
            Path(args.output)
        ),
    }

    summary_path = (
        Path(args.output)
        .with_suffix(".summary.json")
    )

    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print("=== ATLAS LYFE MORPHOLOGY GENERATOR ===")

    for key, value in summary.items():
        print(f"{key}={value}")

    print(f"summary={summary_path}")


if __name__ == "__main__":
    main()
