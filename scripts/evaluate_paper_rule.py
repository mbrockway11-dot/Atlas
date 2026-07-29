"""Out-of-sample test of the derived entry rule -- does the edge survive?

Read-only. Scans teachers, reconstructs their legs, joins candles, then runs a
two-fold cross-teacher evaluation: derive the direction-conditioned entry rule
on one set of teachers and score it on the *other* set (both ways). The headline
number is the out-of-sample win-rate lift -- rule-taken legs' win rate minus the
base rate -- with a proportion test. A lift near zero means the entry state does
not predict winners on unseen traders, which is the honest answer if so.

    .venv/Scripts/python.exe scripts/evaluate_paper_rule.py --top-n 40 --scan 40
"""

from __future__ import annotations

import argparse
import sys

from atlas.investment.hyper_copytrade.basis_reconstruction import (
    reconstruct_realized_legs,
)
from atlas.investment.hyper_copytrade.client import (
    HyperliquidClientError,
    HyperliquidReadClient,
)
from atlas.investment.hyper_copytrade.entry_exit_states import leg_features
from atlas.investment.hyper_copytrade.market_context import CandleSeries
from atlas.investment.hyper_copytrade.ranking import rank_traders
from atlas.investment.hyper_copytrade.significance import test_gap
from atlas.investment.hyper_copytrade.strategy import derive_entry_rule, evaluate_rule
from atlas.investment.hyper_copytrade.trader_style import profile_realized_legs


def _pct(value: float) -> str:
    return f"{value * 100:5.1f}%"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-n", type=int, default=40)
    parser.add_argument("--scan", type=int, default=40)
    parser.add_argument("--min-account-value", type=float, default=100000.0)
    parser.add_argument("--range-lookback-hours", type=float, default=24.0)
    args = parser.parse_args(argv)

    client = HyperliquidReadClient()
    print(f"[provenance] {client.provenance()}")
    try:
        entries = client.fetch_leaderboard()
    except HyperliquidClientError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    rankings = rank_traders(
        entries, top_n=args.top_n, minimum_account_value=args.min_account_value
    )

    print(f"\nScanning top {min(args.scan, len(rankings))} for teachers...")
    teacher_legs: dict[str, list] = {}
    for ranking in rankings[: args.scan]:
        try:
            fills = client.fetch_user_fills(ranking.address)
        except HyperliquidClientError:
            continue
        legs = reconstruct_realized_legs(fills)
        if profile_realized_legs(legs).is_teacher:
            teacher_legs[ranking.address] = legs
    print(f"  {len(teacher_legs)} teachers.")
    if len(teacher_legs) < 4:
        print("Need >=4 teachers for a two-fold split.", file=sys.stderr)
        return 1

    # Candles per coin (clamped to the ~5000-candle cap), then features per teacher.
    lookback_ms = int(args.range_lookback_hours * 3_600_000)
    candle_cap_ms = 4900 * 3_600_000
    spans: dict[str, tuple[int, int]] = {}
    for legs in teacher_legs.values():
        for leg in legs:
            if not leg.entry_observed:
                continue
            lo, hi = leg.entry_time_ms - lookback_ms, leg.exit_time_ms
            prev = spans.get(leg.coin)
            spans[leg.coin] = (min(prev[0], lo), max(prev[1], hi)) if prev else (lo, hi)
    spans = {c: (max(lo, hi - candle_cap_ms), hi) for c, (lo, hi) in spans.items()}
    print(f"  Fetching candles for {len(spans)} coins...")
    candles: dict[str, CandleSeries] = {}
    for coin, (start, end) in spans.items():
        try:
            candles[coin] = CandleSeries.from_raw(
                client.fetch_candles(coin, "1h", start, end)
            )
        except HyperliquidClientError:
            continue

    teacher_features = {
        addr: leg_features(
            legs, candles.get, range_lookback_hours=args.range_lookback_hours
        )
        for addr, legs in teacher_legs.items()
    }

    # Deterministic two-fold split by sorted address (no RNG needed).
    addresses = sorted(teacher_features)
    fold_a = addresses[0::2]
    fold_b = addresses[1::2]
    print(f"\nTwo-fold cross-teacher: A={len(fold_a)} teachers, B={len(fold_b)} teachers")

    print("\n" + "=" * 70)
    print("OUT-OF-SAMPLE ENTRY-RULE EVALUATION")
    print("=" * 70)
    for train, test, name in ((fold_a, fold_b, "A->B"), (fold_b, fold_a, "B->A")):
        train_feats = [f for a in train for f in teacher_features[a]]
        test_feats = [f for a in test for f in teacher_features[a]]
        rule = derive_entry_rule(train_feats)
        result = evaluate_rule(rule, test_feats)
        print(
            f"\n[{name}]  rule: LONG {'>=' if rule.long_side.enter_high else '<='} "
            f"{rule.long_side.threshold:.2f}  "
            f"SHORT {'>=' if rule.short_side.enter_high else '<='} "
            f"{rule.short_side.threshold:.2f}"
        )
        if result is None:
            print("    no scorable test legs.")
            continue
        # Proportion test: taken vs skipped win outcomes (1.0/0.0).
        taken_wins = [1.0] * round(result.taken * result.taken_win_rate) + [0.0] * (
            result.taken - round(result.taken * result.taken_win_rate)
        )
        skipped_wins = [1.0] * round(
            result.skipped * result.skipped_win_rate
        ) + [0.0] * (result.skipped - round(result.skipped * result.skipped_win_rate))
        sig = test_gap(taken_wins, skipped_wins, permutation_iterations=2000)
        pval = f"p={sig.p_value:.3f}" if sig else "p=n/a"
        print(
            f"    base win rate {_pct(result.base_win_rate)}  ->  "
            f"rule-taken {_pct(result.taken_win_rate)}  "
            f"(n={result.taken})   lift {result.win_rate_lift * 100:+.1f}pp  {pval}"
        )
        print(
            f"    mean PnL/leg: base ${result.base_mean_pnl:,.0f}  ->  "
            f"taken ${result.taken_mean_pnl:,.0f}"
        )

    print(
        "\nRead: a lift near 0pp means the entry state does not predict winners "
        "on unseen teachers -- the edge did not survive out-of-sample."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
