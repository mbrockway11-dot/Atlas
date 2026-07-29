"""Blend a roster of Hyperliquid leaders into a paper-capital target book.

Sizing policy: **proportional to equity**. Each leader position contributes a
signed weight equal to its share of that leader's own account equity, so the
leader's leverage and conviction are preserved rather than flattened:

    weight_w[coin] = sign(szi) * position_value / account_value_w

The sign follows ``szi`` (long positive, short negative), and the sum of the
absolute weights for a wallet equals its account leverage. Weights are then
**blended equal-weight across the roster**, netting longs against shorts per
coin: if one leader is long BTC at +0.5 and another short at -0.3, the blended
BTC weight is +0.1.

The blended book is capped at ``maximum_leverage`` (gross, sum of absolute
weights) and scaled to paper capital, giving a signed USD target per coin.
Everything here is pure arithmetic over already-fetched state -- no network,
no execution -- so it is fully offline-testable, and the execution layer (2b)
consumes the target book without re-deriving any of it.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Sequence

from atlas.investment.hyper_copytrade.contracts import WalletState


DEFAULT_MAXIMUM_GROSS_LEVERAGE = 3.0


@dataclass(frozen=True, slots=True)
class TargetPosition:
    """A signed USD target for one coin in the paper book."""

    coin: str
    signed_weight: float
    target_notional: float

    @property
    def direction(self) -> str:
        return "LONG" if self.signed_weight >= 0 else "SHORT"

    def to_dict(self) -> dict[str, Any]:
        return {
            "coin": self.coin,
            "direction": self.direction,
            "signed_weight": self.signed_weight,
            "target_notional": self.target_notional,
        }


@dataclass(frozen=True, slots=True)
class TargetBook:
    """The full blended target book scaled to paper capital."""

    paper_capital: float
    roster_size: int
    gross_leverage_raw: float
    gross_leverage_applied: float
    scale_factor: float
    positions: tuple[TargetPosition, ...]
    net_leverage_raw: float = 0.0
    net_leverage_applied: float = 0.0
    coin_weight_cap: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_capital": self.paper_capital,
            "roster_size": self.roster_size,
            "gross_leverage_raw": self.gross_leverage_raw,
            "gross_leverage_applied": self.gross_leverage_applied,
            "net_leverage_raw": self.net_leverage_raw,
            "net_leverage_applied": self.net_leverage_applied,
            "coin_weight_cap": self.coin_weight_cap,
            "scale_factor": self.scale_factor,
            "positions": [position.to_dict() for position in self.positions],
        }


def wallet_signed_weights(state: WalletState) -> dict[str, float]:
    """Return one wallet's per-coin signed weight (fraction of its equity).

    A wallet with no equity contributes nothing; it cannot be a copy source.
    """
    if state.account_value <= 0.0:
        return {}
    weights: dict[str, float] = defaultdict(float)
    for position in state.positions:
        sign = 1.0 if position.signed_size >= 0 else -1.0
        weights[position.coin] += sign * position.position_value / state.account_value
    return dict(weights)


def blend_targets(
    states: Sequence[WalletState],
    *,
    paper_capital: float,
    maximum_gross_leverage: float = DEFAULT_MAXIMUM_GROSS_LEVERAGE,
    maximum_coin_weight: float | None = None,
    maximum_net_leverage: float | None = None,
    dust_weight: float = 1e-4,
) -> TargetBook:
    """Blend leader wallet states into a capped, scaled signed target book.

    Roster members are blended equal-weight, netting longs against shorts per
    coin. Three risk caps then apply, in order:

    * ``maximum_coin_weight`` -- each coin's absolute weight is clipped to this,
      so no single name dominates (validation showed the edge is breadth, not a
      few concentrated positions). ``None`` disables it.
    * ``maximum_gross_leverage`` -- sum of absolute weights; if exceeded, every
      weight scales down uniformly, preserving the long/short shape.
    * ``maximum_net_leverage`` -- absolute net exposure (sum of signed weights);
      if exceeded, an additional uniform scale-down brings the book back inside
      the limit, so it cannot silently become a one-way directional bet. ``None``
      disables it.

    Coins whose net blended weight is below ``dust_weight`` are dropped so tiny
    netting residuals do not generate orders.
    """
    if paper_capital <= 0.0:
        raise ValueError("paper_capital must be positive.")
    if maximum_gross_leverage <= 0.0:
        raise ValueError("maximum_gross_leverage must be positive.")
    if maximum_coin_weight is not None and maximum_coin_weight <= 0.0:
        raise ValueError("maximum_coin_weight must be positive.")
    if maximum_net_leverage is not None and maximum_net_leverage <= 0.0:
        raise ValueError("maximum_net_leverage must be positive.")
    fundable = [state for state in states if state.account_value > 0.0]
    if not fundable:
        raise ValueError("No fundable wallet states to blend.")

    blended: dict[str, float] = defaultdict(float)
    for state in fundable:
        for coin, weight in wallet_signed_weights(state).items():
            blended[coin] += weight / len(fundable)

    blended = {
        coin: weight
        for coin, weight in blended.items()
        if abs(weight) >= dust_weight
    }

    # Raw (pre-cap) diagnostics, before any concentration clip or scaling.
    gross_raw = sum(abs(weight) for weight in blended.values())
    net_raw = abs(sum(blended.values()))

    # 1. Per-coin concentration cap.
    if maximum_coin_weight is not None:
        blended = {
            coin: max(-maximum_coin_weight, min(maximum_coin_weight, weight))
            for coin, weight in blended.items()
        }

    gross_capped = sum(abs(weight) for weight in blended.values())
    net_capped = abs(sum(blended.values()))

    # 2. Gross-leverage scale, then 3. net-exposure scale -- both uniform, so the
    # smaller (more binding) one governs and the shape is preserved throughout.
    scale_gross = min(1.0, maximum_gross_leverage / gross_capped) if gross_capped > 0.0 else 1.0
    scale_net = (
        min(1.0, maximum_net_leverage / net_capped)
        if maximum_net_leverage is not None and net_capped > 0.0
        else 1.0
    )
    scale = min(scale_gross, scale_net)

    positions = tuple(
        TargetPosition(
            coin=coin,
            signed_weight=weight * scale,
            target_notional=weight * scale * paper_capital,
        )
        for coin, weight in sorted(
            blended.items(), key=lambda kv: abs(kv[1]), reverse=True
        )
    )

    return TargetBook(
        paper_capital=paper_capital,
        roster_size=len(fundable),
        gross_leverage_raw=gross_raw,
        gross_leverage_applied=gross_capped * scale,
        net_leverage_raw=net_raw,
        net_leverage_applied=net_capped * scale,
        coin_weight_cap=maximum_coin_weight,
        scale_factor=scale,
        positions=positions,
    )
