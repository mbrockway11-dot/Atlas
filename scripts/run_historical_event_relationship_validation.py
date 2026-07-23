"""Run the evidence-backed historical transit validation pilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from atlas.historical_validation.pipeline import run_historical_validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--permutations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=19690720)
    parser.add_argument("--registry", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    kwargs = {"permutation_iterations": args.permutations, "seed": args.seed}
    if args.registry is not None:
        kwargs["registry_path"] = args.registry
    if args.output_dir is not None:
        kwargs["output_dir"] = args.output_dir
    report = run_historical_validation(**kwargs)
    print(json.dumps({key: report[key] for key in ("success", "version", "pilot_id", "counts", "output_dir")}, indent=2))


if __name__ == "__main__":
    main()
