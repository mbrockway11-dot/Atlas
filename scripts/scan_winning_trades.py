"""Reconstruct a Hyperliquid wallet's trades and profile its winners.

Read-only. Fetches a wallet's fill history, reconstructs round-trip trades,
and reports win rate, win/loss sizing, holding time and per-direction and
per-coin breakdowns -- the first look at *what a winning trade looks like*,
which is the input to entry/exit-state research.

If no wallet is given, it picks the current best copyable leader.

    .venv/Scripts/python.exe scripts/scan_winning_trades.py
    .venv/Scripts/python.exe scripts/scan_winning_trades.py --address 0x469e...
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import defaultdict

from atlas.investment.hyper_copytrade.client import (
    HyperliquidClientError,
    HyperliquidReadClient,
)
from atlas.investment.hyper_copytrade.ranking import rank_traders
from atlas.investment.hyper_copytrade.selection import (
    NoCopyableLeaderError,
    select_copyable_leader,
)
from atlas.investment.hyper_copytrade.trade_reconstruction import (
    reconstruct_trades,
)


def _usd(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def _resolve_address(client: HyperliquidReadClient, address: str | None) -> str:
    if address:
        return address.strip().lower()
    entries = client.fetch_leaderboard()
    rankings = rank_traders(entries)
    selection = select_copyable_leader(rankings, client)
    print(
        f"Auto-selected best copyable leader: rank {selection.ranking.rank} "
        f"{selection.ranking.address}"
    )
    return selection.ranking.address


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--address", default=None)
    parser.add_argument("--top-winners", type=int, default=8)
    args = parser.parse_args(argv)

    client = HyperliquidReadClient()
    print(f"[provenance] {client.provenance()}")
    try:
        address = _resolve_address(client, args.address)
        fills = client.fetch_user_fills(address)
    except (HyperliquidClientError, NoCopyableLeaderError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    trades = reconstruct_trades(fills)
    closed = [t for t in trades if t.is_closed]
    print(
        f"\nWallet {address}\n"
        f"  {len(fills)} fills -> {len(trades)} trades "
        f"({len(closed)} closed, {len(trades) - len(closed)} still open)"
    )
    if not closed:
        print("  (no closed trades to profile)")
        return 0

    wins = [t for t in closed if t.is_win]
    losses = [t for t in closed if not t.is_win]
    win_rate = len(wins) / len(closed)
    gross_win = sum(t.realized_pnl for t in wins)
    gross_loss = sum(t.realized_pnl for t in losses)
    avg_win = statistics.mean([t.realized_pnl for t in wins]) if wins else 0.0
    avg_loss = statistics.mean([t.realized_pnl for t in losses]) if losses else 0.0
    profit_factor = (gross_win / abs(gross_loss)) if gross_loss else float("inf")
    durations_min = [t.duration_ms / 60000.0 for t in closed]

    print(
        f"\n  win rate       {win_rate * 100:5.1f}%  ({len(wins)}W / {len(losses)}L)\n"
        f"  gross win      {_usd(gross_win)}\n"
        f"  gross loss     {_usd(gross_loss)}\n"
        f"  net realized   {_usd(gross_win + gross_loss)}\n"
        f"  profit factor  {profit_factor:.2f}\n"
        f"  avg win        {_usd(avg_win)}\n"
        f"  avg loss       {_usd(avg_loss)}\n"
        f"  median hold    {statistics.median(durations_min):.1f} min\n"
        f"  win/loss hold  {_mean_hold(wins):.1f} / {_mean_hold(losses):.1f} min"
    )

    print("\n  by direction:")
    for direction in ("LONG", "SHORT"):
        d = [t for t in closed if t.direction == direction]
        if d:
            dw = sum(1 for t in d if t.is_win) / len(d)
            print(
                f"    {direction:5}  {len(d):>4} trades  "
                f"{dw * 100:5.1f}% win  {_usd(sum(t.realized_pnl for t in d))} pnl"
            )

    by_coin: dict[str, list] = defaultdict(list)
    for t in closed:
        by_coin[t.coin].append(t)
    print("\n  top coins by realized pnl:")
    ranked_coins = sorted(
        by_coin.items(), key=lambda kv: sum(t.realized_pnl for t in kv[1]), reverse=True
    )
    for coin, ts in ranked_coins[:6]:
        wr = sum(1 for t in ts if t.is_win) / len(ts)
        print(
            f"    {coin:>8}  {len(ts):>4} trades  {wr * 100:5.1f}% win  "
            f"{_usd(sum(t.realized_pnl for t in ts))}"
        )

    print(f"\n  top {args.top_winners} winning trades:")
    for t in sorted(wins, key=lambda x: x.realized_pnl, reverse=True)[: args.top_winners]:
        print(
            f"    {t.coin:>8}  {t.direction:5}  entry {t.entry_price:>12,.4f}  "
            f"exit {t.exit_price:>12,.4f}  {t.duration_ms / 60000.0:>7.1f} min  "
            f"{_usd(t.realized_pnl):>12}"
        )
    return 0


def _mean_hold(trades: list) -> float:
    if not trades:
        return 0.0
    return statistics.mean([t.duration_ms / 60000.0 for t in trades])


if __name__ == "__main__":
    raise SystemExit(main())
