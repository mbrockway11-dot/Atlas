"""Per-cycle paper mechanics for the copy-trade forward runner.

The forward runner (``scripts/run_forward_copytrade_paper.py``) blends a live
leader roster into a signed :class:`~atlas.investment.hyper_copytrade.mirror.TargetBook`
and then, every cycle, has to do three things to the persistent paper account:
accrue perp funding on the book it already holds, rebalance that book toward the
new signed target, and mark the result to live prices. Those three operations
are pure arithmetic over an account, a target and a price map -- no network and
no roster logic -- so they live here and are unit-tested offline. The script
owns all I/O: fetching the roster, fetching mids, and persistence.

Rebalancing runs each leg through the real paper-execution service
(:func:`atlas.investment.execution.service.run_paper_execution`), so the same
short-capable, risk-limited, paper-only plane that guards the alpha forward run
guards this one -- there is no separate, weaker fill path here.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace

from atlas.investment.execution.account_store import (
    AccountSnapshot,
    account_from_mapping,
)
from atlas.investment.execution.contracts import OrderIntent, RiskLimits
from atlas.investment.execution.instruments import (
    SYMBOL_ALIASES,
    require_paper_instrument,
)
from atlas.investment.execution.service import run_paper_execution
from atlas.investment.hyper_copytrade.contracts import WalletState
from atlas.investment.hyper_copytrade.mirror import TargetBook


def tradable_perp_coins() -> frozenset[str]:
    """The Hyperliquid coin names the paper plane can both paper-trade and short.

    The execution plane only knows the symbols in its instrument registry, and
    only a subset of those are short-enabled perps. A leader's position in any
    other coin cannot be mirrored -- the order would be rejected
    ``UNREGISTERED_INSTRUMENT`` (or ``INSTRUMENT_SHORT_DISABLED`` for a spot
    proxy). This derives the real tradable universe from the registry rather
    than hard-coding it, so adding a perp instrument automatically widens it.
    """
    coins: set[str] = set()
    for coin in SYMBOL_ALIASES:
        try:
            instrument = require_paper_instrument(coin)
        except (KeyError, ValueError):
            continue
        if instrument.short_enabled:
            coins.add(coin.upper())
    return frozenset(coins)


@dataclass(frozen=True, slots=True)
class UniverseCoverage:
    """How much of a roster's gross exposure survived the tradable-universe filter."""

    roster_gross: float
    tradable_gross: float
    dropped_coins: tuple[str, ...]

    @property
    def coverage_fraction(self) -> float:
        """Fraction of roster gross notional that is tradable (1.0 if roster flat)."""
        return self.tradable_gross / self.roster_gross if self.roster_gross > 0.0 else 1.0


def restrict_states_to_universe(
    states: Sequence[WalletState], universe: frozenset[str]
) -> tuple[list[WalletState], UniverseCoverage]:
    """Drop each leader's positions in coins outside ``universe``, keeping equity.

    Account value is preserved, so a leader's tradable positions keep their
    original fraction-of-equity sizing -- we copy only the tradable slice at the
    leader's own conviction, we do not re-lever it to fill the gap. Returns the
    filtered states (those left with at least one tradable position) and a
    coverage report naming what was dropped, so the untradable exposure is
    visible in the log rather than silently vanishing.
    """
    roster_gross = 0.0
    tradable_gross = 0.0
    dropped: set[str] = set()
    filtered: list[WalletState] = []
    for state in states:
        kept = []
        for position in state.positions:
            roster_gross += position.position_value
            if position.coin.upper() in universe:
                tradable_gross += position.position_value
                kept.append(position)
            else:
                dropped.add(position.coin.upper())
        if kept:
            filtered.append(replace(state, positions=tuple(kept)))
    coverage = UniverseCoverage(
        roster_gross=roster_gross,
        tradable_gross=tradable_gross,
        dropped_coins=tuple(sorted(dropped)),
    )
    return filtered, coverage


def positions_map(account: AccountSnapshot) -> dict[str, float]:
    """Return ``{ASSET: signed_quantity}`` for the account's open positions."""
    out: dict[str, float] = {}
    pos = getattr(account, "positions", {}) or {}
    values = pos.values() if isinstance(pos, dict) else pos
    for position in values:
        if isinstance(position, dict):
            out[str(position.get("asset")).upper()] = float(position.get("quantity", 0.0))
        else:
            out[str(position.asset).upper()] = float(position.quantity)
    return out


def net_liquidation(account: AccountSnapshot, prices: dict[str, float]) -> float:
    """Cash plus the mark-to-market value of every held position."""
    equity = float(getattr(account, "cash", 0.0))
    for asset, quantity in positions_map(account).items():
        equity += quantity * prices.get(asset, 0.0)
    return equity


def gross_notional(account: AccountSnapshot, prices: dict[str, float]) -> float:
    """Sum of absolute position notionals at the given prices."""
    return sum(
        abs(quantity) * prices.get(asset, 0.0)
        for asset, quantity in positions_map(account).items()
    )


def accrue_funding(
    account: AccountSnapshot,
    prices: dict[str, float],
    *,
    elapsed_days: float,
    funding_bps_per_day: float,
) -> tuple[AccountSnapshot, float]:
    """Debit perp funding on the held book for ``elapsed_days`` and return it.

    Funding is charged on gross notional (both longs and shorts pay in this
    simple, conservative model) at ``funding_bps_per_day``. The debit reduces
    cash only; positions are untouched. A non-positive elapsed span is a no-op,
    so a same-cycle re-run does not double-charge.
    """
    if elapsed_days <= 0.0 or funding_bps_per_day <= 0.0:
        return account, 0.0
    funding_paid = funding_bps_per_day / 10_000.0 * elapsed_days * gross_notional(
        account, prices
    )
    charged = AccountSnapshot(
        cash=float(getattr(account, "cash", 0.0)) - funding_paid,
        positions=getattr(account, "positions", {}) or {},
    )
    return charged, funding_paid


def target_notionals(book: TargetBook) -> dict[str, float]:
    """Project a blended target book to ``{COIN: signed_notional}``."""
    return {
        position.coin.upper(): float(position.target_notional)
        for position in book.positions
    }


def fit_targets_to_cash(
    targets: dict[str, float],
    capital_base: float,
    *,
    fee_buffer_bps: float = 50.0,
) -> tuple[dict[str, float], float]:
    """Scale a signed target book so its long side is fundable, shape preserved.

    The paper execution plane is cash-settled: opening a long consumes cash
    equal to its notional, opening a short frees cash (the proceeds). Because
    equity equals ``cash + sum_long - sum_short``, the account's cash stays
    non-negative after rebalancing exactly when **net long notional does not
    exceed equity** -- a path-independent bound, so ``capital_base`` is the
    account's net-liquidation equity, not its momentary free cash. A book whose
    net long exceeds that would have its last legs silently rejected for
    insufficient cash, so the held book would stop matching the reported one.
    This scales every target by one factor so net long notional lands just
    inside the base, with a small buffer for the fees each fill draws. A
    net-short or already-covered book is returned unchanged (scale 1.0).
    """
    longs = sum(value for value in targets.values() if value > 0.0)
    shorts = -sum(value for value in targets.values() if value < 0.0)
    net_long = longs - shorts
    budget = capital_base * (1.0 - fee_buffer_bps / 10_000.0)
    if net_long <= 0.0 or net_long <= budget:
        return dict(targets), 1.0
    scale = budget / net_long
    return {coin: value * scale for coin, value in targets.items()}, scale


def rebalance_to_targets(
    account: AccountSnapshot,
    targets: dict[str, float],
    prices: dict[str, float],
    *,
    limits: RiskLimits,
    minimum_rebalance_notional: float,
    strategy_id: str = "forward_copytrade_mirror",
) -> tuple[AccountSnapshot, int]:
    """Trade the account from its current book toward ``targets`` (signed USD).

    For every asset in either the target or the current book, the signed
    quantity delta is computed at the live price; deltas whose notional is below
    ``minimum_rebalance_notional`` are skipped so netting dust does not churn
    fees. **Cash-freeing trades execute first**: because the plane is
    cash-settled, orders are placed in ascending signed-notional-delta order, so
    every sell (closing a long, opening a short) settles its proceeds into cash
    before any buy has to draw on it -- otherwise a large new buy early in the
    cycle could trip ``INSUFFICIENT_CASH`` while the offsetting sell still waits.
    Each surviving delta is submitted as one paper order through
    :func:`run_paper_execution`; rejected orders (risk-limit trips) leave the
    account unchanged and are simply not counted. Returns the updated account
    and the number of fills. Assets with no live price are skipped -- an unknown
    price must not be treated as zero, which would look like a close.
    """
    current = positions_map(account)
    plan: list[tuple[float, str, float]] = []  # (signed_notional_delta, asset, price)
    for asset in set(targets) | set(current):
        price = prices.get(asset)
        if not price or price <= 0.0:
            continue
        delta_quantity = targets.get(asset, 0.0) / price - current.get(asset, 0.0)
        delta_notional = delta_quantity * price
        if abs(delta_notional) < minimum_rebalance_notional:
            continue
        plan.append((delta_notional, asset, price))
    plan.sort(key=lambda leg: leg[0])  # sells (negative) first, then buys

    fills = 0
    for delta_notional, asset, price in plan:
        report = run_paper_execution(
            intent=OrderIntent(
                asset=asset,
                side="BUY" if delta_notional > 0 else "SELL",
                quantity=round(abs(delta_notional) / price, 8),
                reference_price=price,
                strategy_id=strategy_id,
                evidence_id=f"forward_copytrade:{asset}",
            ),
            account=account,
            limits=limits,
            write_outputs=False,
        )
        if report["risk"]["approved"]:
            fills += len(report.get("fills", []))
            account = account_from_mapping(report["account_after"])
    return account, fills
