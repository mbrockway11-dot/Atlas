"""Forward paper run of the Hyperliquid copy-trade mirror book.

Read-only market data; paper-only, short-capable execution, no signing path.
Each cycle: pick a leader roster, fetch each selected leader's live positions,
blend them into a capped signed target book (per-coin, gross and net caps),
accrue perp funding on the book already held, rebalance the persistent paper
account toward the new target, mark to market at live mids, and append one row
to a forward equity log. The account persists across cycles, so running this on
a schedule builds a genuine out-of-sample-in-time track record -- the one test
the registry backtests could not do, and the only thing that can decisively
settle the selection-metric and roster-size questions.

Two roster sources:

  * ``registry`` (default) -- rank the already-scanned teacher registry by
    per-leg Sharpe, no leaderboard fetch; the sole network calls are one live
    wallet-state fetch per *selected* teacher, plus one mids fetch.
  * ``leaderboard`` -- rank the live leaderboard by weekly PnL and walk to the
    top-N copyable wallets.

Books persist under ``output/investment_forward_copytrade/<book>/``. ``--ab``
runs the standard experiment from ONE shared roster/state/mark fetch: two copy
books ``cap025`` (per-coin cap 0.25) and ``cap050`` (0.50) that isolate the
cap's effect, plus two benchmark books ``btc`` and ``ewmajors`` (fixed long
baskets through the same plane) so a copy book's edge is its return OVER the
benchmark, not raw return that is mostly crypto beta. A single ad-hoc copy book
runs under ``--book <name>``.

    .venv/Scripts/python.exe scripts/run_forward_copytrade_paper.py --ab
    .venv/Scripts/python.exe scripts/run_forward_copytrade_paper.py --book main
    .venv/Scripts/python.exe scripts/run_forward_copytrade_paper.py --ab --mark-only
    # then schedule, e.g. Windows Task Scheduler / cron
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from atlas.investment.execution.account_store import AccountSnapshot, account_from_mapping
from atlas.investment.execution.contracts import RiskLimits
from atlas.investment.hyper_copytrade.client import (
    HyperliquidClientError,
    HyperliquidReadClient,
)
from atlas.investment.hyper_copytrade.contracts import VALID_METRICS, VALID_WINDOWS, WalletState
from atlas.investment.hyper_copytrade.mirror import blend_targets
from atlas.investment.hyper_copytrade.paper_forward import (
    accrue_funding,
    fit_targets_to_cash,
    net_liquidation,
    positions_map,
    rebalance_to_targets,
    restrict_states_to_universe,
    target_notionals,
    tradable_perp_coins,
)
from atlas.investment.hyper_copytrade.ranking import rank_traders
from atlas.investment.hyper_copytrade.selection import (
    NoCopyableLeaderError,
    select_copyable_roster,
    select_registry_roster_by_skill,
)
from atlas.investment.hyper_copytrade.teacher_registry import (
    DEFAULT_REGISTRY_PATH,
    load_teacher_records,
)

BASE_DIR = Path("output/investment_forward_copytrade")

# The standard experiment run by --ab. Two COPY books share one roster/state/mark
# fetch and differ only in their per-coin cap, so their curves isolate its effect
# (cap025 = breadth-first, cap050 = lets big-name conviction show through). Two
# BENCHMARK books hold fixed long baskets through the same plane (same funding,
# fees, marks) -- so a copy book's edge is its return OVER the benchmark, not its
# raw return, which in a rising market is mostly crypto beta.
COPY_BOOKS: tuple[tuple[str, float], ...] = (("cap025", 0.25), ("cap050", 0.50))
_BENCHMARK_BASKETS: dict[str, tuple[str, ...]] = {
    "btc": ("BTC",),
    "ewmajors": ("BTC", "ETH", "SOL", "BNB", "XRP"),
}


def _book_paths(name: str) -> tuple[Path, Path, Path, Path]:
    directory = BASE_DIR / name
    return (
        directory,
        directory / "forward_account.json",
        directory / "forward_state.json",
        directory / "forward_equity_log.csv",
    )


def _write_json_atomic(path: Path, payload: object) -> None:
    """Persist JSON atomically (.tmp + replace), per the repo's write convention.

    A plain write that is interrupted mid-flush can leave a truncated account or
    state file, corrupting the persistent book. Writing to a sibling .tmp and
    renaming makes the swap atomic on the same filesystem.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", "utf-8")
    tmp.replace(path)


def _copy_target_fn(cap: float):
    """A book target builder that mirrors the leaders with a given per-coin cap."""
    def build(states, prices, equity, args):
        if not states:
            return {}, None
        book = blend_targets(
            states,
            paper_capital=equity or args.initial_cash,
            maximum_gross_leverage=args.max_gross_leverage,
            maximum_coin_weight=cap,
            maximum_net_leverage=args.max_net_leverage,
        )
        targets, _ = fit_targets_to_cash(target_notionals(book), equity)
        return targets, book
    return build


def _benchmark_target_fn(basket: tuple[str, ...]):
    """A book target builder that holds a fixed equal-weight long basket (net 1x).

    Independent of the roster -- it is the market-beta control the copy books are
    measured against. Rebalances to the basket every cycle so it stays ~1x long.
    """
    def build(states, prices, equity, args):
        base = equity or args.initial_cash
        coins = [coin for coin in basket if prices.get(coin, 0.0) > 0.0]
        if not coins:
            return {}, None
        per_coin = base / len(coins)
        targets, _ = fit_targets_to_cash({coin: per_coin for coin in coins}, equity)
        return targets, None
    return build


def _usd(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def _roster_states(
    client: HyperliquidReadClient, args: argparse.Namespace
) -> list[WalletState]:
    """Fetch live wallet states for the selected roster (source-dependent)."""
    if args.source == "registry":
        if not args.registry_path.exists():
            print(f"No registry at {args.registry_path}. Run build_teacher_registry.py "
                  "first, or use --source leaderboard.", file=sys.stderr)
            return []
        roster = select_registry_roster_by_skill(
            load_teacher_records(args.registry_path),
            size=args.roster,
            minimum_legs=args.min_legs,
        )
        if not roster:
            print(f"No registry teachers with >= {args.min_legs} legs.", file=sys.stderr)
            return []
        addresses = [member.address for member in roster]
        print(f"Roster: top {len(addresses)} of {args.roster} by per-leg Sharpe "
              f"(>= {args.min_legs} legs).")
    else:
        entries = client.fetch_leaderboard()
        rankings = rank_traders(
            entries, window=args.window, metric=args.metric,
            top_n=args.top_n, minimum_account_value=args.min_account_value,
        )
        try:
            selection = select_copyable_roster(rankings, client, size=args.roster)
        except NoCopyableLeaderError as error:
            print(f"Roster selection failed: {error}", file=sys.stderr)
            return []
        # These states were already fetched during copyability probing; reuse them.
        return [member.state for member in selection.members]

    states: list[WalletState] = []
    for address in addresses:
        try:
            state = client.fetch_wallet_state(address)
        except HyperliquidClientError:
            print(f"  (skip {address[:12]}: wallet-state fetch failed)")
            continue
        if state.account_value > 0.0 and state.positions:
            states.append(state)
    return states


def refuse_live(book_names: list[str]) -> int:
    """The --live path. It does not, and will not, place a live order."""
    print("=" * 70)
    print("LIVE EXECUTION IS DISABLED BY DESIGN. No order will be placed.")
    print("=" * 70)
    print("\nForward-paper readiness (see docs/GO_LIVE_CRITERIA.md):")
    for name in book_names:
        _, _, _, equity_log = _book_paths(name)
        days, equities = 0, []
        if equity_log.exists():
            rows = list(csv.DictReader(equity_log.open(encoding="utf-8")))
            days = len({r["timestamp"][:10] for r in rows})
            equities = [float(r["equity"]) for r in rows]
        peak, max_dd = (equities[0] if equities else 0.0), 0.0
        for equity in equities:
            peak = max(peak, equity)
            max_dd = min(max_dd, equity / peak - 1.0) if peak else 0.0
        print(f"  [{name}] forward track {days} day(s) [gate 1 >= 90]  "
              f"max drawdown {max_dd * 100:.1f}% [gate 3 <= 30%]")
    print("\nTo go live you must, yourself: review the checklist, set up your own "
          "venue credentials in your own environment, and place a small, risk-capped "
          "first order by hand. This assistant will not do any of those steps.")
    return 3


def _process_book(
    name: str,
    target_fn,
    cap_display: float | None,
    *,
    now: datetime,
    prices: dict[str, float],
    states: list[WalletState] | None,
    do_rebalance: bool,
    args: argparse.Namespace,
) -> None:
    """Run one persistent paper book for one cycle from shared inputs.

    ``target_fn`` builds the signed target notionals for this book from the
    shared roster ``states`` (a copy book) or ignores them (a benchmark basket).
    Every book resumes its own account, accrues funding, rebalances to its own
    target, marks at the SAME prices and appends to its own equity log -- so
    across books only the intended knob (the cap, or copy-vs-benchmark) differs.
    """
    directory, account_json, state_json, equity_log = _book_paths(name)
    directory.mkdir(parents=True, exist_ok=True)

    if account_json.exists():
        account = account_from_mapping(json.loads(account_json.read_text("utf-8")))
    else:
        account = AccountSnapshot(cash=float(args.initial_cash))
    state = json.loads(state_json.read_text("utf-8")) if state_json.exists() else {}
    last_run = state.get("last_run")

    starting_equity = net_liquidation(account, prices)

    funding_paid = 0.0
    if last_run:
        elapsed_days = max(0.0, (now - datetime.fromisoformat(last_run)).total_seconds() / 86_400.0)
        account, funding_paid = accrue_funding(
            account, prices, elapsed_days=elapsed_days,
            funding_bps_per_day=args.funding_bps_per_day,
        )

    fills, roster_size, book = 0, 0, None
    if do_rebalance:
        targets, book = target_fn(states, prices, starting_equity, args)
        if targets:
            roster_size = book.roster_size if book is not None else 0
            limits = RiskLimits(
                allow_short_positions=True, maximum_leverage=args.max_gross_leverage,
                maximum_order_notional=max(5_000.0, args.initial_cash),
                maximum_asset_notional=max(10_000.0, args.initial_cash),
                maximum_gross_exposure=max(20_000.0, args.initial_cash * args.max_gross_leverage),
                maximum_daily_loss=args.initial_cash,  # forward-paper: don't halt on a down day
            )
            account, fills = rebalance_to_targets(
                account, targets, prices,
                limits=limits, minimum_rebalance_notional=args.min_rebalance_notional,
            )

    ending_equity = net_liquidation(account, prices)

    _write_json_atomic(account_json, account.to_dict())
    _write_json_atomic(state_json, {"last_run": now.isoformat()})
    pos = positions_map(account)
    longs = {a: q for a, q in pos.items() if q > 1e-9}
    shorts = {a: q for a, q in pos.items() if q < -1e-9}
    gross = sum(abs(q) * prices.get(a, 0.0) for a, q in pos.items())
    net = sum(q * prices.get(a, 0.0) for a, q in pos.items())
    row = {
        "timestamp": now.isoformat(), "book": name, "source": args.source,
        "coin_cap": cap_display if cap_display is not None else "",
        "equity": round(ending_equity, 2),
        "cash": round(float(getattr(account, "cash", 0.0)), 2),
        "funding_paid": round(funding_paid, 4), "fills": fills,
        "roster_size": roster_size, "n_long": len(longs), "n_short": len(shorts),
        "gross_exposure": round(gross, 2), "net_exposure": round(net, 2),
    }
    header = not equity_log.exists()
    with equity_log.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(row))
        if header:
            writer.writeheader()
        writer.writerow(row)

    tag = f"  cap {cap_display:g}" if cap_display is not None else "  benchmark"
    if book is not None:
        tag = (f"  gross {book.gross_leverage_applied:.2f}x net "
               f"{book.net_leverage_applied:+.2f}x cap {cap_display:g}")
    print(f"  [{name:8}] equity {_usd(starting_equity)}->{_usd(ending_equity)}  "
          f"{len(longs)}L/{len(shorts)}S gross {_usd(gross)} net {_usd(net)}  "
          f"fills {fills} funding {_usd(funding_paid)}{tag}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("registry", "leaderboard"), default="registry")
    parser.add_argument("--registry-path", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--roster", type=int, default=12)
    parser.add_argument("--min-legs", type=int, default=20)
    parser.add_argument("--window", choices=VALID_WINDOWS, default="week")
    parser.add_argument("--metric", choices=VALID_METRICS, default="pnl")
    parser.add_argument("--top-n", type=int, default=50)
    parser.add_argument("--min-account-value", type=float, default=100_000.0)
    parser.add_argument("--initial-cash", type=float, default=100_000.0)
    parser.add_argument("--max-gross-leverage", type=float, default=3.0)
    parser.add_argument("--max-coin-weight", type=float, default=0.25)
    parser.add_argument("--max-net-leverage", type=float, default=1.0,
                        help="Cash-settled plane funds net long <= equity, so 1.0x is "
                             "the real ceiling; shorts fund longs, so gross can exceed it.")
    parser.add_argument("--funding-bps-per-day", type=float, default=3.0)
    parser.add_argument("--min-rebalance-notional", type=float, default=50.0)
    parser.add_argument("--book", default="main",
                        help="Name of the persistent book (subdir under the state dir).")
    parser.add_argument("--ab", action="store_true",
                        help="Run the standard experiment: copy books cap025/cap050 plus "
                             "btc/ewmajors benchmarks, all from one shared fetch.")
    parser.add_argument("--mark-only", action="store_true",
                        help="Revalue the held books at live mids and log; do NOT rebalance.")
    parser.add_argument("--live", action="store_true",
                        help="INERT by design: refuses to execute; prints the go-live checklist.")
    args = parser.parse_args(argv)

    # Each book: (name, target_builder, cap_display). Copy books mirror the
    # leaders; benchmark books hold a fixed basket as the market-beta control.
    if args.ab:
        books = [(name, _copy_target_fn(cap), cap) for name, cap in COPY_BOOKS]
        books += [(name, _benchmark_target_fn(basket), None)
                  for name, basket in _BENCHMARK_BASKETS.items()]
    else:
        books = [(args.book, _copy_target_fn(args.max_coin_weight), args.max_coin_weight)]

    if args.live:
        return refuse_live([name for name, *_ in books])

    now = datetime.now(timezone.utc)
    client = HyperliquidReadClient()
    print(f"[provenance] {client.provenance()}")

    try:
        prices = client.fetch_all_mids()
    except HyperliquidClientError as error:
        print(f"ERROR fetching mids: {error}", file=sys.stderr)
        return 1

    # Fetch the roster and leader states ONCE, so every book blends from the same
    # inputs and the only difference between them is their per-coin cap.
    states: list[WalletState] | None = None
    if not args.mark_only:
        raw_states = _roster_states(client, args)
        # The paper plane can only execute the registered short-enabled perps;
        # restrict the blend to that universe so the held book is the mirror we
        # can actually trade, not its registered-coin residue, and report any
        # coverage dropped so the loss is visible rather than silent.
        filtered, coverage = restrict_states_to_universe(raw_states, tradable_perp_coins())
        if coverage.dropped_coins:
            print(f"Universe: kept {coverage.coverage_fraction * 100:.0f}% of roster "
                  f"gross; dropped untradable {', '.join(coverage.dropped_coins)}")
        if not filtered:
            print("No tradable roster positions this cycle; marking held books only.")
        else:
            states = filtered

    print(f"\nForward copy-trade cycle {now.isoformat()}:")
    for name, target_fn, cap in books:
        _process_book(name, target_fn, cap, now=now, prices=prices,
                      states=states, do_rebalance=not args.mark_only, args=args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
