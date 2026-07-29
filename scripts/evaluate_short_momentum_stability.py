"""Stability test for the SHORT-momentum lead across many teacher splits.

Read-only. A single two-fold split cannot tell a real edge from one that a few
teachers happen to carry -- exactly the ambiguity that made the 41-teacher
result a mirage. This runs many random teacher-level splits: each time, fit the
momentum rule on a random half of teachers and score it on the other half's
SHORT legs, then look at the *distribution* of the out-of-sample PnL/leg lift.

Teacher-level (not leg-level) splitting respects clustering -- a wallet's legs
never span train and test. The verdict is blunt: if most splits are positive
with a consistent learned direction, the SHORT-momentum lead is robust; if the
lift straddles zero, it was fold luck.

    .venv/Scripts/python.exe scripts/evaluate_short_momentum_stability.py --repeats 100
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

import numpy as np

from atlas.investment.hyper_copytrade.analysis_pipeline import features_by_teacher
from atlas.investment.hyper_copytrade.client import HyperliquidReadClient
from atlas.investment.hyper_copytrade.strategy import (
    derive_entry_rule,
    evaluate_rule,
    momentum_of,
)
from atlas.investment.hyper_copytrade.teacher_registry import (
    DEFAULT_REGISTRY_PATH,
    iter_teacher_legs,
    load_teacher_records,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY_PATH))
    parser.add_argument("--range-lookback-hours", type=float, default=24.0)
    parser.add_argument("--repeats", type=int, default=100)
    args = parser.parse_args(argv)

    records = load_teacher_records(Path(args.registry))
    teacher_legs = dict(iter_teacher_legs(records))
    print(f"Registry: {len(teacher_legs)} teachers.")
    if len(teacher_legs) < 8:
        print("Need >=8 teachers.", file=sys.stderr)
        return 1

    client = HyperliquidReadClient()
    teacher_features = features_by_teacher(
        client, teacher_legs, range_lookback_hours=args.range_lookback_hours,
        progress=True,
    )
    addresses = sorted(teacher_features)

    pnl_lifts: list[float] = []
    win_lifts: list[float] = []
    short_low_count = 0  # times the rule learned "short only when momentum low"
    usable = 0

    for repeat in range(args.repeats):
        rng = np.random.default_rng(repeat)
        shuffled = list(addresses)
        rng.shuffle(shuffled)
        half = len(shuffled) // 2
        train_addr, test_addr = shuffled[:half], shuffled[half:]

        train_feats = [f for a in train_addr for f in teacher_features[a]]
        test_short = [
            f
            for a in test_addr
            for f in teacher_features[a]
            if f.direction == "SHORT"
        ]
        rule = derive_entry_rule(train_feats, momentum_of)
        result = evaluate_rule(rule, test_short, momentum_of)
        if result is None or result.taken == 0:
            continue
        usable += 1
        pnl_lifts.append(result.taken_mean_pnl - result.base_mean_pnl)
        win_lifts.append(result.win_rate_lift)
        if not rule.short_side.enter_high:  # "<=" == short only when momentum low
            short_low_count += 1

    if not pnl_lifts:
        print("No usable splits.", file=sys.stderr)
        return 1

    positive = sum(1 for x in pnl_lifts if x > 0)
    print("\n" + "=" * 66)
    print(f"SHORT-MOMENTUM STABILITY  ({usable} usable random teacher splits)")
    print("=" * 66)
    print(
        f"  PnL/leg lift:  median ${statistics.median(pnl_lifts):+,.0f}   "
        f"mean ${statistics.fmean(pnl_lifts):+,.0f}\n"
        f"                 p25 ${np.percentile(pnl_lifts, 25):+,.0f}  "
        f"p75 ${np.percentile(pnl_lifts, 75):+,.0f}  "
        f"[min ${min(pnl_lifts):+,.0f}, max ${max(pnl_lifts):+,.0f}]\n"
        f"  splits with POSITIVE PnL lift: {positive}/{len(pnl_lifts)} "
        f"({positive / len(pnl_lifts) * 100:.0f}%)\n"
        f"  win-rate lift: median {statistics.median(win_lifts) * 100:+.1f}pp\n"
        f"  learned 'short when momentum low' in {short_low_count}/{usable} "
        f"splits ({short_low_count / usable * 100:.0f}%)"
    )
    print(
        "\nRead: >~80% positive with consistent direction => robust lead; "
        "~50% => fold luck."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
