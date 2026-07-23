"""Run the Atlas symbolic-behavior association pilot."""

from __future__ import annotations

import argparse
import json

from atlas.symbolic_behavior.pipeline import run_population_symbolic_feature_index, run_symbolic_behavior_validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default=None)
    parser.add_argument("--permutations", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=8_675_309)
    parser.add_argument("--all-profiles", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.all_profiles:
        kwargs = {"force": args.force}
        if args.registry:
            kwargs["registry_path"] = args.registry
        print(json.dumps(run_population_symbolic_feature_index(**kwargs), indent=2))
        return
    kwargs = {"permutation_iterations": args.permutations, "seed": args.seed}
    if args.registry:
        kwargs["registry_path"] = args.registry
    print(json.dumps(run_symbolic_behavior_validation(**kwargs), indent=2))


if __name__ == "__main__":
    main()
