"""Find discrete swing-trader 'teachers' among the top Hyperliquid leaders.

Read-only. Ranks the leaderboard, then classifies each top wallet's trading
style from one fill page. Discrete swing traders -- crisp directional entries
that flatten -- are the wallets worth learning entry/exit states from; HFT and
persistent market-makers are filtered out.

    .venv/Scripts/python.exe scripts/scan_swing_teachers.py --scan 25
"""

from __future__ import annotations

import argparse
import sys

from atlas.investment.hyper_copytrade.client import (
    HyperliquidClientError,
    HyperliquidReadClient,
)
from atlas.investment.hyper_copytrade.ranking import rank_traders
from atlas.investment.hyper_copytrade.trade_reconstruction import (
    reconstruct_trades,
)
from atlas.investment.hyper_copytrade.trader_style import (
    TraderStyle,
    classify_style,
)


def _usd(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-n", type=int, default=50)
    parser.add_argument("--min-account-value", type=float, default=100000.0)
    parser.add_argument("--scan", type=int, default=25, help="Wallets to classify.")
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
    print(f"Classifying style of the top {min(args.scan, len(rankings))} ranked wallets...\n")

    header = (
        f"{'#':>3}  {'address':42}  {'style':16}  {'fills/trade':>11}  "
        f"{'closed':>6}  {'medHold':>8}  {'win%':>5}"
    )
    print(header)
    print("-" * len(header))

    teachers = []
    for ranking in rankings[: args.scan]:
        try:
            fills = client.fetch_user_fills(ranking.address)
            trades = reconstruct_trades(fills)
            profile = classify_style(trades, len(fills))
        except HyperliquidClientError:
            continue
        flag = " <= TEACHER" if profile.is_teacher else ""
        hold = (
            f"{profile.median_hold_minutes:,.0f}m"
            if profile.style is not TraderStyle.INSUFFICIENT_DATA
            else "-"
        )
        win = (
            f"{profile.win_rate * 100:.0f}"
            if profile.style is not TraderStyle.INSUFFICIENT_DATA
            else "-"
        )
        print(
            f"{ranking.rank:>3}  {ranking.address:42}  {profile.style.value:16}  "
            f"{profile.fills_per_closed_trade:>11.1f}  "
            f"{profile.closed_trade_count:>6}  {hold:>8}  {win:>5}{flag}"
        )
        if profile.is_teacher:
            teachers.append((ranking, profile))

    print(
        f"\n{len(teachers)} discrete swing teacher(s) found in the top {args.scan}:"
    )
    for ranking, profile in teachers:
        print(
            f"  rank {ranking.rank:>3}  {ranking.address}  "
            f"wk PnL {_usd(ranking.pnl)}  {profile.closed_trade_count} closed trades  "
            f"{profile.median_hold_minutes:,.0f}m median hold  "
            f"{profile.win_rate * 100:.0f}% win"
        )
    if not teachers:
        print("  (none — try raising --scan or lowering the account floor)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
