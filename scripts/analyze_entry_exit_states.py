"""Derive optimal entry/exit states from Hyperliquid teachers' winning legs.

Read-only, end to end: rank the leaderboard, keep wallets that pass the
loosened leg-based teacher gate, reconstruct their realized legs, join each
entry to its coin's candles, and aggregate winners vs losers into
price-vs-range (entry) and holding-time (exit) distributions.

    .venv/Scripts/python.exe scripts/analyze_entry_exit_states.py \
        --top-n 25 --scan 20 --range-lookback-hours 24
"""

from __future__ import annotations

import argparse
import sys

from atlas.investment.hyper_copytrade.client import (
    HyperliquidClientError,
    HyperliquidReadClient,
)
from atlas.investment.hyper_copytrade.basis_reconstruction import (
    reconstruct_realized_legs,
)
from atlas.investment.hyper_copytrade.entry_exit_states import (
    Distribution,
    leg_features,
    per_teacher_states,
    summarize_states,
)
from atlas.investment.hyper_copytrade.market_context import CandleSeries
from atlas.investment.hyper_copytrade.ranking import rank_traders
from atlas.investment.hyper_copytrade.significance import test_gap
from atlas.investment.hyper_copytrade.trade_reconstruction import reconstruct_trades
from atlas.investment.hyper_copytrade.trader_style import (
    classify_style,
    profile_realized_legs,
)


def _fmt(dist: Distribution | None, unit: str = "") -> str:
    if dist is None:
        return "(no data)"
    return (
        f"n={dist.count:<5} median={dist.median:7.2f}{unit}  "
        f"[p25 {dist.p25:7.2f}{unit} .. p75 {dist.p75:7.2f}{unit}]"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-n", type=int, default=25)
    parser.add_argument("--min-account-value", type=float, default=100000.0)
    parser.add_argument("--scan", type=int, default=20)
    parser.add_argument("--range-lookback-hours", type=float, default=24.0)
    parser.add_argument(
        "--strict-swing",
        action="store_true",
        help="Use the strict discrete-swing (round-trip) gate, not the loosened bar.",
    )
    parser.add_argument("--permutation-iterations", type=int, default=5000)
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

    # 1. Find teachers and collect their realized legs, keyed by teacher so the
    #    aggregation can count each trader once rather than by leg volume.
    gate = "strict discrete-swing" if args.strict_swing else "loosened leg-based"
    print(f"\nScanning top {min(args.scan, len(rankings))} for teachers ({gate})...")
    teacher_legs: dict[str, list] = {}
    for ranking in rankings[: args.scan]:
        try:
            fills = client.fetch_user_fills(ranking.address)
        except HyperliquidClientError:
            continue
        legs = reconstruct_realized_legs(fills)
        if args.strict_swing:
            is_teacher = classify_style(reconstruct_trades(fills), len(fills)).is_teacher
        else:
            is_teacher = profile_realized_legs(legs).is_teacher
        if not is_teacher:
            continue
        teacher_legs[ranking.address] = legs
    all_legs = [leg for legs in teacher_legs.values() for leg in legs]
    print(f"  {len(teacher_legs)} teachers, {len(all_legs)} realized legs collected.")
    if not all_legs:
        print("No teacher legs to analyze.", file=sys.stderr)
        return 1

    # 2. Fetch candles once per coin, covering every entry-observed leg's span.
    # Clamp each span to stay under Hyperliquid's ~5000-candle cap: at 1h that is
    # ~208 days ending at the coin's most recent exit. Legs with entries older
    # than the covered window simply get no range_position (None), rather than
    # the whole fetch silently truncating and starving every leg of coverage.
    lookback_ms = int(args.range_lookback_hours * 3_600_000)
    candle_cap_ms = 4900 * 3_600_000
    spans: dict[str, tuple[int, int]] = {}
    for leg in all_legs:
        if not leg.entry_observed:
            continue
        lo = leg.entry_time_ms - lookback_ms
        hi = leg.exit_time_ms
        if leg.coin in spans:
            prev = spans[leg.coin]
            spans[leg.coin] = (min(prev[0], lo), max(prev[1], hi))
        else:
            spans[leg.coin] = (lo, hi)
    spans = {
        coin: (max(lo, hi - candle_cap_ms), hi)
        for coin, (lo, hi) in spans.items()
    }

    print(f"  Fetching 1h candles for {len(spans)} coins...")
    candle_cache: dict[str, CandleSeries] = {}
    for coin, (start, end) in spans.items():
        try:
            raw = client.fetch_candles(coin, "1h", start, end)
            candle_cache[coin] = CandleSeries.from_raw(raw)
        except HyperliquidClientError:
            continue

    # 3. Feature, per teacher and pooled.
    teacher_features = {
        address: leg_features(
            legs, candle_cache.get, range_lookback_hours=args.range_lookback_hours
        )
        for address, legs in teacher_legs.items()
    }
    features = [f for feats in teacher_features.values() for f in feats]
    report = summarize_states(features)
    per_teacher = per_teacher_states(teacher_features)

    print("\n" + "=" * 70)
    print("OPTIMAL ENTRY/EXIT STATES  (winners vs losers)")
    print("=" * 70)

    print(f"\nENTRY STATE  --  price vs recent {args.range_lookback_hours:.0f}h range")
    print("  0.0 = entered at range low (pullback)   1.0 = at range high (breakout)")
    print(f"    pooled winners:  {_fmt(report.winner_range_position)}")
    print(f"    pooled losers :  {_fmt(report.loser_range_position)}")
    print(f"    per-teacher winners: {_fmt(per_teacher.winner_range_position)}")
    print(f"    per-teacher losers : {_fmt(per_teacher.loser_range_position)}")

    print("\nEXIT STATE  --  holding time (minutes)")
    print(f"    pooled winners:  {_fmt(report.winner_hold_minutes, 'm')}")
    print(f"    pooled losers :  {_fmt(report.loser_hold_minutes, 'm')}")
    print(f"    per-teacher winners: {_fmt(per_teacher.winner_hold_minutes, 'm')}")
    print(f"    per-teacher losers : {_fmt(per_teacher.loser_hold_minutes, 'm')}")

    # Significance of the pooled winner-vs-loser gaps.
    print("\nSIGNIFICANCE (pooled legs, Mann-Whitney U + permutation)")
    _significance(
        [f.range_position for f in features if f.is_win and f.range_position is not None],
        [f.range_position for f in features if not f.is_win and f.range_position is not None],
        "entry range position",
        args.permutation_iterations,
    )
    _significance(
        [f.holding_minutes for f in features if f.is_win],
        [f.holding_minutes for f in features if not f.is_win],
        "exit holding time",
        args.permutation_iterations,
    )

    print("\nENTRY range position, winners by direction:")
    for direction in ("LONG", "SHORT"):
        vals = [
            f.range_position
            for f in features
            if f.is_win and f.direction == direction and f.range_position is not None
        ]
        if vals:
            vals.sort()
            mid = vals[len(vals) // 2]
            print(f"    {direction:5}  n={len(vals):<5} median range position {mid:.2f}")
    return 0


def _significance(winners, losers, label, iterations):
    result = test_gap(winners, losers, permutation_iterations=iterations)
    if result is None:
        print(f"    {label:22}  insufficient data")
        return
    verdict = "SIGNIFICANT" if result.significant else "not significant"
    print(
        f"    {label:22}  gap {result.median_gap:+.2f}  "
        f"MWU p={result.p_value:.2e}  perm p={result.permutation_p_value:.4f}  "
        f"effect r={result.rank_biserial:+.2f}  -> {verdict}"
    )


def _delta(
    winner: Distribution | None, loser: Distribution | None, label: str
) -> None:
    if winner is None or loser is None:
        print(f"    -> insufficient data to contrast {label}.")
        return
    gap = winner.median - loser.median
    if abs(gap) < 1e-9:
        print(f"    -> winners and losers overlap on {label}: no edge on this axis.")
    else:
        print(f"    -> winners' median {label} differs by {gap:+.2f} vs losers.")


if __name__ == "__main__":
    raise SystemExit(main())
