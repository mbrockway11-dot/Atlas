"""Offline tests for the Hyperliquid copy-trading tracker.

Fixtures mirror the real API shapes captured from the live endpoints, so no
network access is needed. These lock the load-bearing invariants: the
short=negative-size sign convention, the PnL ranking order, and the selection
walk that skips uncopyable wallets.
"""

from __future__ import annotations

import pytest

from atlas.investment.hyper_copytrade.contracts import (
    LeaderPosition,
    LeaderboardEntry,
    WalletState,
)
from atlas.investment.hyper_copytrade.mirror import (
    blend_targets,
    wallet_signed_weights,
)
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
from atlas.investment.hyper_copytrade.client import (
    HyperliquidClientError,
    HyperliquidReadClient,
)
from atlas.investment.execution.contracts import RiskLimits
from atlas.investment.execution.account_store import AccountSnapshot
from atlas.investment.hyper_copytrade.ranking import (
    best_trader,
    per_leg_sharpe,
    rank_teachers_by_skill,
    rank_traders,
)
from atlas.investment.hyper_copytrade.selection import (
    CopyabilityPolicy,
    NoCopyableLeaderError,
    select_copyable_leader,
    select_copyable_roster,
    select_registry_roster_by_skill,
)
from atlas.investment.hyper_copytrade.teacher_registry import (
    RegisteredLeg,
    TeacherRecord,
)


def _row(address: str, account_value: str, week_pnl: str, week_roi: str) -> dict:
    """A leaderboard row shaped like the real ``leaderboardRows`` element."""
    return {
        "ethAddress": address,
        "accountValue": account_value,
        "displayName": None,
        "windowPerformances": [
            ["day", {"pnl": "0", "roi": "0", "vlm": "0"}],
            ["week", {"pnl": week_pnl, "roi": week_roi, "vlm": "1000000"}],
            ["month", {"pnl": "0", "roi": "0", "vlm": "0"}],
            ["allTime", {"pnl": "0", "roi": "0", "vlm": "0"}],
        ],
    }


def _clearinghouse(account_value: str, positions: list[dict]) -> dict:
    notional = sum(
        float(p["position"]["positionValue"]) for p in positions
    )
    return {
        "marginSummary": {
            "accountValue": account_value,
            "totalNtlPos": str(notional),
            "totalMarginUsed": "0",
        },
        "assetPositions": positions,
    }


def _asset_position(coin: str, szi: str, leverage: int) -> dict:
    return {
        "type": "oneWay",
        "position": {
            "coin": coin,
            "szi": szi,
            "leverage": {"type": "cross", "value": leverage},
            "entryPx": "100",
            "positionValue": str(abs(float(szi)) * 100),
            "unrealizedPnl": "10",
            "returnOnEquity": "0.1",
        },
    }


ADDR_A = "0x" + "a" * 40
ADDR_B = "0x" + "b" * 40
ADDR_C = "0x" + "c" * 40


def test_leaderboard_entry_parses_windows():
    entry = LeaderboardEntry.from_row(_row(ADDR_A, "500000", "12345.6", "0.25"))
    assert entry.address == ADDR_A
    assert entry.account_value == 500000.0
    assert entry.performance("week").pnl == pytest.approx(12345.6)
    assert entry.performance("week").roi == pytest.approx(0.25)


def test_malformed_address_rejected():
    with pytest.raises(ValueError):
        LeaderboardEntry.from_row(_row("not-an-address", "1", "1", "1"))


def test_short_is_negative_size_long_is_positive():
    short = LeaderPosition.from_asset_position(_asset_position("XRP", "-500", 20))
    long = LeaderPosition.from_asset_position(_asset_position("BTC", "5", 25))
    assert short.direction == "SHORT"
    assert short.signed_size < 0
    assert long.direction == "LONG"
    assert long.signed_size > 0


def test_ranking_orders_by_pnl_descending():
    entries = [
        LeaderboardEntry.from_row(_row(ADDR_A, "500000", "100", "0.9")),
        LeaderboardEntry.from_row(_row(ADDR_B, "500000", "9000", "0.1")),
        LeaderboardEntry.from_row(_row(ADDR_C, "500000", "500", "0.5")),
    ]
    ranked = rank_traders(entries, metric="pnl", minimum_account_value=0.0)
    assert [r.address for r in ranked] == [ADDR_B, ADDR_C, ADDR_A]
    assert best_trader(ranked).address == ADDR_B


def test_ranking_drops_dust_below_account_floor():
    entries = [
        LeaderboardEntry.from_row(_row(ADDR_A, "5000", "99999", "9.9")),
        LeaderboardEntry.from_row(_row(ADDR_B, "500000", "100", "0.1")),
    ]
    ranked = rank_traders(entries, metric="pnl", minimum_account_value=100000.0)
    assert [r.address for r in ranked] == [ADDR_B]


class _FakeSource:
    """A WalletStateSource backed by a fixture dict, counting fetches."""

    def __init__(self, states: dict[str, dict]):
        self._states = states
        self.calls = 0

    def fetch_wallet_state(self, address: str) -> WalletState:
        self.calls += 1
        return WalletState.from_clearinghouse_state(address, self._states[address])


def test_selection_skips_empty_wallets_to_first_copyable():
    entries = [
        LeaderboardEntry.from_row(_row(ADDR_A, "9000000", "500", "0.01")),
        LeaderboardEntry.from_row(_row(ADDR_B, "800000", "400", "0.02")),
        LeaderboardEntry.from_row(_row(ADDR_C, "600000", "300", "0.03")),
    ]
    ranked = rank_traders(entries, metric="pnl", minimum_account_value=0.0)
    source = _FakeSource(
        {
            ADDR_A: _clearinghouse("0", []),  # vault: empty, skip
            ADDR_B: _clearinghouse("60000", []),  # funded but flat, skip
            ADDR_C: _clearinghouse(
                "600000",
                [
                    _asset_position("BTC", "10000", 25),  # positionValue 1,000,000
                    _asset_position("XRP", "-8000", 20),  # positionValue 800,000
                ],
            ),
        }
    )
    selection = select_copyable_leader(ranked, source)
    assert selection.ranking.address == ADDR_C
    assert [s.reason for s in selection.skipped] == [
        "no_open_positions",
        "no_open_positions",
    ]
    assert {p.direction for p in selection.state.positions} == {"LONG", "SHORT"}


def test_selection_respects_probe_budget():
    entries = [
        LeaderboardEntry.from_row(_row(ADDR_A, "900000", "500", "0.01")),
        LeaderboardEntry.from_row(_row(ADDR_B, "800000", "400", "0.02")),
    ]
    ranked = rank_traders(entries, metric="pnl", minimum_account_value=0.0)
    source = _FakeSource(
        {ADDR_A: _clearinghouse("0", []), ADDR_B: _clearinghouse("0", [])}
    )
    policy = CopyabilityPolicy(maximum_candidates_to_probe=1)
    with pytest.raises(NoCopyableLeaderError):
        select_copyable_leader(ranked, source, policy=policy)
    assert source.calls == 1  # budget honored: only one wallet probed


def test_roster_collects_top_n_copyable():
    entries = [
        LeaderboardEntry.from_row(_row(ADDR_A, "9000000", "500", "0.01")),
        LeaderboardEntry.from_row(_row(ADDR_B, "800000", "400", "0.02")),
        LeaderboardEntry.from_row(_row(ADDR_C, "600000", "300", "0.03")),
    ]
    ranked = rank_traders(entries, metric="pnl", minimum_account_value=0.0)
    source = _FakeSource(
        {
            ADDR_A: _clearinghouse("0", []),  # vault, skipped
            ADDR_B: _clearinghouse(
                "800000", [_asset_position("BTC", "10000", 25)]
            ),
            ADDR_C: _clearinghouse(
                "600000", [_asset_position("XRP", "-8000", 20)]
            ),
        }
    )
    roster = select_copyable_roster(ranked, source, size=2)
    assert roster.addresses == (ADDR_B, ADDR_C)
    assert [s.reason for s in roster.skipped] == ["no_open_positions"]


def test_roster_raises_when_too_few_copyable():
    entries = [LeaderboardEntry.from_row(_row(ADDR_A, "900000", "500", "0.01"))]
    ranked = rank_traders(entries, metric="pnl", minimum_account_value=0.0)
    source = _FakeSource({ADDR_A: _clearinghouse("0", [])})
    with pytest.raises(NoCopyableLeaderError):
        select_copyable_roster(ranked, source, size=2)


def test_wallet_signed_weights_sign_and_magnitude():
    # $1M account, $500k long BTC + $300k short XRP -> +0.5 BTC, -0.3 XRP
    state = WalletState.from_clearinghouse_state(
        ADDR_A,
        _clearinghouse(
            "1000000",
            [
                {
                    "type": "oneWay",
                    "position": {
                        "coin": "BTC", "szi": "5", "leverage": {"value": 10},
                        "entryPx": "100000", "positionValue": "500000",
                        "unrealizedPnl": "0", "returnOnEquity": "0",
                    },
                },
                {
                    "type": "oneWay",
                    "position": {
                        "coin": "XRP", "szi": "-300000", "leverage": {"value": 10},
                        "entryPx": "1", "positionValue": "300000",
                        "unrealizedPnl": "0", "returnOnEquity": "0",
                    },
                },
            ],
        ),
    )
    weights = wallet_signed_weights(state)
    assert weights["BTC"] == pytest.approx(0.5)
    assert weights["XRP"] == pytest.approx(-0.3)


def _state(address, account_value, positions):
    return WalletState.from_clearinghouse_state(
        address, _clearinghouse(str(account_value), positions)
    )


def test_blend_nets_longs_and_shorts_across_roster():
    # Wallet 1: long BTC 0.5 of equity. Wallet 2: short BTC 0.3 of equity.
    # Equal-weight blend -> (0.5 - 0.3) / 2 = +0.1 BTC.
    w1 = _state(ADDR_A, 1000000, [_asset_position("BTC", "5000", 10)])  # +500k/1M
    w2 = _state(ADDR_B, 1000000, [_asset_position("BTC", "-3000", 10)])  # -300k/1M
    book = blend_targets([w1, w2], paper_capital=100000, maximum_gross_leverage=3.0)
    btc = next(p for p in book.positions if p.coin == "BTC")
    assert btc.signed_weight == pytest.approx(0.1)
    assert btc.direction == "LONG"
    assert btc.target_notional == pytest.approx(10000.0)


def test_blend_caps_gross_leverage():
    # Single wallet at 6x gross; cap at 3x should halve every weight.
    w = _state(
        ADDR_A,
        1000000,
        [
            _asset_position("BTC", "40000", 25),  # 4,000,000 notional -> 4.0
            _asset_position("XRP", "-20000", 20),  # 2,000,000 notional -> -2.0
        ],
    )
    book = blend_targets([w], paper_capital=100000, maximum_gross_leverage=3.0)
    assert book.gross_leverage_raw == pytest.approx(6.0)
    assert book.gross_leverage_applied == pytest.approx(3.0)
    assert book.scale_factor == pytest.approx(0.5)


def test_blend_caps_per_coin_concentration():
    # HYPE at 1.5x of equity, BTC at 0.1x. Coin cap 0.5 clips HYPE, leaves BTC.
    w = _state(
        ADDR_A,
        1000000,
        [
            _asset_position("HYPE", "15000", 10),  # 1,500,000 notional -> 1.5
            _asset_position("BTC", "1000", 10),  # 100,000 notional -> 0.1
        ],
    )
    book = blend_targets(
        [w], paper_capital=100000, maximum_gross_leverage=10.0, maximum_coin_weight=0.5
    )
    hype = next(p for p in book.positions if p.coin == "HYPE")
    btc = next(p for p in book.positions if p.coin == "BTC")
    assert abs(hype.signed_weight) == pytest.approx(0.5)  # clipped
    assert abs(btc.signed_weight) == pytest.approx(0.1)  # untouched
    assert book.coin_weight_cap == 0.5


def test_blend_caps_net_exposure():
    # Fully-short book: BTC -1.0, ETH -0.5 -> net -1.5, gross 1.5. Net cap 0.5
    # scales the whole book down (gross cap 3.0 is not binding).
    w = _state(
        ADDR_A,
        1000000,
        [
            _asset_position("BTC", "-10000", 10),  # -1,000,000 -> -1.0
            _asset_position("ETH", "-5000", 10),  # -500,000 -> -0.5
        ],
    )
    book = blend_targets(
        [w], paper_capital=100000, maximum_gross_leverage=3.0, maximum_net_leverage=0.5
    )
    assert book.net_leverage_raw == pytest.approx(1.5)
    assert book.net_leverage_applied == pytest.approx(0.5)
    assert book.scale_factor == pytest.approx(1.0 / 3.0)  # 0.5 / 1.5
    # Net cap binds, so gross is scaled down with it (1.5 * 1/3 = 0.5).
    gross_applied = sum(abs(p.signed_weight) for p in book.positions)
    assert gross_applied == pytest.approx(0.5)


def _fill(coin, side, sz, px, start, dir_, pnl=0.0, t=0, fee=0.0):
    return {
        "coin": coin, "side": side, "sz": str(sz), "px": str(px),
        "startPosition": str(start), "dir": dir_, "closedPnl": str(pnl),
        "time": t, "fee": str(fee),
    }


def test_reconstruct_simple_long_win():
    from atlas.investment.hyper_copytrade.trade_reconstruction import (
        reconstruct_trades,
    )
    fills = [
        _fill("BTC", "B", 2, 100, 0, "Open Long", 0.0, t=1000, fee=1.0),
        _fill("BTC", "A", 2, 110, 2, "Close Long", 20.0, t=2000, fee=1.0),
    ]
    trades = reconstruct_trades(fills)
    assert len(trades) == 1
    trade = trades[0]
    assert trade.direction == "LONG"
    assert trade.is_closed and trade.is_win
    assert trade.entry_price == pytest.approx(100.0)
    assert trade.exit_price == pytest.approx(110.0)
    assert trade.realized_pnl == pytest.approx(20.0)
    assert trade.total_fees == pytest.approx(2.0)
    assert trade.net_pnl == pytest.approx(18.0)
    assert trade.duration_ms == 1000


def test_reconstruct_short_loss():
    from atlas.investment.hyper_copytrade.trade_reconstruction import (
        reconstruct_trades,
    )
    fills = [
        _fill("XRP", "A", 100, 1.0, 0, "Open Short", 0.0, t=1),
        _fill("XRP", "B", 100, 1.1, -100, "Close Short", -10.0, t=2),
    ]
    trades = reconstruct_trades(fills)
    assert len(trades) == 1
    assert trades[0].direction == "SHORT"
    assert trades[0].is_closed
    assert not trades[0].is_win
    assert trades[0].realized_pnl == pytest.approx(-10.0)


def test_reconstruct_add_then_scale_out():
    from atlas.investment.hyper_copytrade.trade_reconstruction import (
        reconstruct_trades,
    )
    # Open 2 @100, add 2 @120 (avg entry 110), close 2 @150, close 2 @150.
    fills = [
        _fill("ETH", "B", 2, 100, 0, "Open Long", 0.0, t=1),
        _fill("ETH", "B", 2, 120, 2, "Open Long", 0.0, t=2),
        _fill("ETH", "A", 2, 150, 4, "Close Long", 90.0, t=3),
        _fill("ETH", "A", 2, 150, 2, "Close Long", 80.0, t=4),
    ]
    trades = reconstruct_trades(fills)
    assert len(trades) == 1
    trade = trades[0]
    assert trade.entry_price == pytest.approx(110.0)  # size-weighted
    assert trade.exit_price == pytest.approx(150.0)
    assert trade.realized_pnl == pytest.approx(170.0)
    assert trade.peak_size == pytest.approx(4.0)
    assert trade.leg_count == 4


def test_reconstruct_open_only_is_unclosed():
    from atlas.investment.hyper_copytrade.trade_reconstruction import (
        reconstruct_trades,
    )
    fills = [_fill("SOL", "B", 5, 200, 0, "Open Long", 0.0, t=1)]
    trades = reconstruct_trades(fills)
    assert len(trades) == 1
    assert not trades[0].is_closed
    assert not trades[0].is_win  # unclosed never counts as a win


def test_reconstruct_separates_sequential_trades():
    from atlas.investment.hyper_copytrade.trade_reconstruction import (
        reconstruct_trades,
    )
    fills = [
        _fill("BTC", "B", 1, 100, 0, "Open Long", 0.0, t=1),
        _fill("BTC", "A", 1, 110, 1, "Close Long", 10.0, t=2),
        _fill("BTC", "B", 1, 120, 0, "Open Long", 0.0, t=3),
        _fill("BTC", "A", 1, 115, 1, "Close Long", -5.0, t=4),
    ]
    trades = reconstruct_trades(fills)
    assert len(trades) == 2
    assert [t.is_win for t in trades] == [True, False]


def test_basis_legs_emit_one_per_close():
    from atlas.investment.hyper_copytrade.basis_reconstruction import (
        reconstruct_realized_legs,
    )
    # Persistent long that never flattens: 2 opens, 2 partial closes -> 2 legs.
    fills = [
        _fill("BTC", "B", 4, 100, 0, "Open Long", 0.0, t=1000),
        _fill("BTC", "B", 4, 120, 4, "Open Long", 0.0, t=2000),  # avg basis 110
        _fill("BTC", "A", 3, 150, 8, "Close Long", 120.0, t=3000),
        _fill("BTC", "A", 2, 160, 5, "Close Long", 100.0, t=4000),
        # still 3 long open at the end -> no third leg
    ]
    legs = reconstruct_realized_legs(fills)
    assert len(legs) == 2
    assert all(leg.direction == "LONG" for leg in legs)
    assert legs[0].entry_price == pytest.approx(110.0)  # avg cost basis
    assert legs[0].exit_price == pytest.approx(150.0)
    assert legs[0].closed_pnl == pytest.approx(120.0)
    assert legs[0].is_win
    assert legs[0].holding_ms == 3000 - 1500  # exit - weighted avg entry time


def test_basis_holding_uses_weighted_entry_time():
    from atlas.investment.hyper_copytrade.basis_reconstruction import (
        reconstruct_realized_legs,
    )
    # Equal-size opens at t=1000 and t=3000 -> weighted entry time 2000.
    fills = [
        _fill("ETH", "B", 5, 100, 0, "Open Long", 0.0, t=1000),
        _fill("ETH", "B", 5, 100, 5, "Open Long", 0.0, t=3000),
        _fill("ETH", "A", 10, 110, 10, "Close Long", 100.0, t=5000),
    ]
    legs = reconstruct_realized_legs(fills)
    assert len(legs) == 1
    assert legs[0].entry_time_ms == 2000
    assert legs[0].holding_ms == 3000


def test_basis_handles_short_and_flip():
    from atlas.investment.hyper_copytrade.basis_reconstruction import (
        reconstruct_realized_legs,
    )
    # Short 5 @100, then buy 8 @90: closes the 5 short (win), flips to long 3.
    fills = [
        _fill("XRP", "A", 5, 100, 0, "Open Short", 0.0, t=1),
        _fill("XRP", "B", 8, 90, -5, "Short > Long", 50.0, t=2),
        _fill("XRP", "A", 3, 95, 3, "Close Long", 15.0, t=3),
    ]
    legs = reconstruct_realized_legs(fills)
    assert len(legs) == 2
    assert legs[0].direction == "SHORT"
    assert legs[0].size == pytest.approx(5.0)
    assert legs[0].closed_pnl == pytest.approx(50.0)
    assert legs[0].entry_observed
    assert legs[1].direction == "LONG"  # the flipped residual, later closed
    assert legs[1].entry_price == pytest.approx(90.0)
    assert legs[1].entry_observed


def test_basis_close_without_observed_open_flags_unobserved():
    from atlas.investment.hyper_copytrade.basis_reconstruction import (
        reconstruct_realized_legs,
    )
    # The window starts mid-position: first fill is a Close with no prior Open.
    # PnL is still real; entry is not observed.
    fills = [
        _fill("BTC", "A", 3, 150, 3, "Close Long", 120.0, t=1000),
    ]
    legs = reconstruct_realized_legs(fills)
    assert len(legs) == 1
    assert legs[0].is_win
    assert legs[0].closed_pnl == pytest.approx(120.0)
    assert not legs[0].entry_observed


def test_leg_teacher_gate_loosened_includes_persistent():
    from atlas.investment.hyper_copytrade.basis_reconstruction import RealizedLeg
    from atlas.investment.hyper_copytrade.trader_style import (
        profile_realized_legs,
    )
    # 25 legs, ~30 min holds -> passes the loosened bar.
    legs = [
        RealizedLeg("BTC", "LONG", 100, 0, 101, 30 * 60000, 1.0, 5.0, True)
        for _ in range(25)
    ]
    profile = profile_realized_legs(legs)
    assert profile.is_teacher
    assert profile.leg_count == 25
    assert profile.median_hold_minutes == pytest.approx(30.0)


def test_leg_teacher_gate_rejects_scalper():
    from atlas.investment.hyper_copytrade.basis_reconstruction import RealizedLeg
    from atlas.investment.hyper_copytrade.trader_style import (
        profile_realized_legs,
    )
    # 40 legs but 30-second holds -> scalper, rejected.
    legs = [
        RealizedLeg("BTC", "LONG", 100, 0, 101, 30 * 1000, 1.0, 5.0, True)
        for _ in range(40)
    ]
    profile = profile_realized_legs(legs)
    assert not profile.is_teacher
    assert profile.reject_reason == "scalper_hold_too_short"


def _candle(t, low, high):
    return {"t": t, "T": t + 3_600_000, "o": low, "c": high, "h": high, "l": low}


def test_range_position_places_entry_in_recent_range():
    from atlas.investment.hyper_copytrade.market_context import CandleSeries
    hour = 3_600_000
    # 24 candles, range low=100 high=200, each 1h before entry at t=25h.
    candles = [_candle(i * hour, 100, 200) for i in range(24)]
    series = CandleSeries.from_raw(candles)
    entry_time = 25 * hour
    lookback = 24 * hour
    # entry at 100 = bottom of range -> 0.0; at 200 -> 1.0; at 150 -> 0.5
    assert series.range_position(100, entry_time, lookback) == pytest.approx(0.0)
    assert series.range_position(200, entry_time, lookback) == pytest.approx(1.0)
    assert series.range_position(150, entry_time, lookback) == pytest.approx(0.5)
    # breakout above the prior high -> > 1
    assert series.range_position(220, entry_time, lookback) == pytest.approx(1.2)


def test_momentum_before_is_leading_return():
    from atlas.investment.hyper_copytrade.market_context import CandleSeries
    hour = 3_600_000
    # Close rises 100 -> 110 across the window before entry -> +10% momentum.
    candles = [
        {"t": i * hour, "T": i * hour + hour, "o": 100 + i, "c": 100 + i,
         "h": 100 + i, "l": 100 + i}
        for i in range(11)  # closes 100..110
    ]
    series = CandleSeries.from_raw(candles)
    mom = series.momentum_before(11 * hour, 24 * hour)
    assert mom == pytest.approx((110 - 100) / 100)  # +0.10
    # Thin window -> None.
    assert series.momentum_before(1 * hour, 24 * hour) is None


def test_momentum_selector_and_rule_learn_direction():
    from atlas.investment.hyper_copytrade.entry_exit_states import LegFeature
    from atlas.investment.hyper_copytrade.strategy import (
        derive_entry_rule,
        evaluate_rule,
        momentum_of,
    )
    # Winners follow positive momentum, losers negative -> rule learns enter_high.
    feats = (
        [LegFeature("BTC", "LONG", True, 1, 0, None, momentum=0.05) for _ in range(6)]
        + [LegFeature("BTC", "LONG", False, -1, 0, None, momentum=-0.05) for _ in range(6)]
    )
    rule = derive_entry_rule(feats, momentum_of)
    assert rule.long_side.enter_high is True
    result = evaluate_rule(rule, feats, momentum_of)
    assert result is not None
    assert result.win_rate_lift == pytest.approx(0.5)


def test_range_before_excludes_entry_bar_and_thin_windows():
    from atlas.investment.hyper_copytrade.market_context import CandleSeries
    hour = 3_600_000
    candles = [_candle(i * hour, 100, 200) for i in range(5)]
    series = CandleSeries.from_raw(candles)
    # Only 2 candles before t=2h -> below minimum_candles(3) -> None
    assert series.range_position(150, 2 * hour, 24 * hour) is None
    # Degenerate flat range -> None
    flat = CandleSeries.from_raw([_candle(i * hour, 100, 100) for i in range(10)])
    assert flat.range_position(100, 11 * hour, 24 * hour) is None


def test_summarize_states_contrasts_winners_and_losers():
    from atlas.investment.hyper_copytrade.entry_exit_states import (
        LegFeature,
        summarize_states,
    )
    # Winners entered low in range (pullbacks), losers entered high (chased).
    winners = [
        LegFeature("BTC", "LONG", True, 100.0, 120.0, 0.1) for _ in range(10)
    ]
    losers = [
        LegFeature("BTC", "LONG", False, -50.0, 30.0, 0.9) for _ in range(10)
    ]
    report = summarize_states(winners + losers)
    assert report.winning_legs == 10
    assert report.losing_legs == 10
    assert report.winner_range_position.median == pytest.approx(0.1)
    assert report.loser_range_position.median == pytest.approx(0.9)
    assert report.winner_hold_minutes.median == pytest.approx(120.0)
    assert report.loser_hold_minutes.median == pytest.approx(30.0)


def test_summarize_states_range_needs_candle_coverage():
    from atlas.investment.hyper_copytrade.entry_exit_states import (
        LegFeature,
        summarize_states,
    )
    # Holding time always present; range_position None when no candles.
    feats = [
        LegFeature("BTC", "LONG", True, 10.0, 60.0, None) for _ in range(5)
    ]
    report = summarize_states(feats)
    assert report.winner_hold_minutes.count == 5
    assert report.winner_range_position is None  # no coverage -> no range stats


def test_significance_detects_clear_separation():
    from atlas.investment.hyper_copytrade.significance import test_gap
    winners = [0.8 + 0.01 * i for i in range(40)]  # ~0.8-1.2
    losers = [0.4 + 0.01 * i for i in range(40)]   # ~0.4-0.8, lower
    result = test_gap(winners, losers, permutation_iterations=1000)
    assert result is not None
    assert result.median_gap == pytest.approx(0.4, abs=0.05)
    assert result.p_value < 0.05
    assert result.permutation_p_value < 0.05
    assert result.significant
    assert result.rank_biserial > 0.5  # winners clearly higher


def test_significance_finds_no_edge_when_identical():
    from atlas.investment.hyper_copytrade.significance import test_gap
    winners = [0.5 + 0.001 * i for i in range(40)]
    losers = [0.5 + 0.001 * i for i in range(40)]  # same distribution
    result = test_gap(winners, losers, permutation_iterations=1000)
    assert result is not None
    assert not result.significant
    assert result.p_value > 0.05


def test_significance_none_on_empty_group():
    from atlas.investment.hyper_copytrade.significance import test_gap
    assert test_gap([0.5], [], permutation_iterations=100) is None


def test_per_teacher_states_counts_each_teacher_once():
    from atlas.investment.hyper_copytrade.entry_exit_states import (
        LegFeature,
        per_teacher_states,
    )
    # Teacher A: 1000 winning legs at 0.9. Teacher B: 2 winning legs at 0.3.
    # Pooled would be dominated by A; per-teacher gives medians [0.9, 0.3].
    teacher_features = {
        "A": [LegFeature("BTC", "LONG", True, 1.0, 60.0, 0.9) for _ in range(1000)],
        "B": [LegFeature("ETH", "LONG", True, 1.0, 60.0, 0.3) for _ in range(2)],
    }
    states = per_teacher_states(teacher_features)
    assert states.n_teachers == 2
    # median of per-teacher medians [0.9, 0.3] = 0.6, not ~0.9
    assert states.winner_range_position.median == pytest.approx(0.6)


def test_entry_rule_side_logic():
    from atlas.investment.hyper_copytrade.entry_exit_states import LegFeature
    from atlas.investment.hyper_copytrade.strategy import EntryRule, _Side
    # LONG enters high (>=0.4); SHORT enters low (<=0.3) -- both sides honored.
    rule = EntryRule(
        long_side=_Side(threshold=0.4, enter_high=True),
        short_side=_Side(threshold=0.3, enter_high=False),
    )
    assert rule.takes(LegFeature("BTC", "LONG", True, 0, 0, 0.5))
    assert not rule.takes(LegFeature("BTC", "LONG", True, 0, 0, 0.2))
    assert rule.takes(LegFeature("BTC", "SHORT", True, 0, 0, 0.2))
    assert not rule.takes(LegFeature("BTC", "SHORT", True, 0, 0, 0.5))
    assert not rule.takes(LegFeature("BTC", "LONG", True, 0, 0, None))


def test_derive_entry_rule_learns_side_and_threshold_from_train():
    from atlas.investment.hyper_copytrade.entry_exit_states import LegFeature
    from atlas.investment.hyper_copytrade.strategy import derive_entry_rule
    # LONG winners HIGH (0.8) losers low (0.4) -> enter_high, threshold 0.6.
    # SHORT winners LOW (0.2) losers high (0.6) -> enter_low, threshold 0.4.
    features = (
        [LegFeature("BTC", "LONG", True, 1, 0, 0.8) for _ in range(5)]
        + [LegFeature("BTC", "LONG", False, -1, 0, 0.4) for _ in range(5)]
        + [LegFeature("BTC", "SHORT", True, 1, 0, 0.2) for _ in range(5)]
        + [LegFeature("BTC", "SHORT", False, -1, 0, 0.6) for _ in range(5)]
    )
    rule = derive_entry_rule(features)
    assert rule.long_side.enter_high is True
    assert rule.long_side.threshold == pytest.approx(0.6)
    assert rule.short_side.enter_high is False
    assert rule.short_side.threshold == pytest.approx(0.4)


def test_evaluate_rule_reports_out_of_sample_lift():
    from atlas.investment.hyper_copytrade.entry_exit_states import LegFeature
    from atlas.investment.hyper_copytrade.strategy import EntryRule, _Side, evaluate_rule
    rule = EntryRule(
        long_side=_Side(threshold=0.5, enter_high=True),
        short_side=_Side(threshold=0.5, enter_high=True),
    )
    # Taken (LONG high) legs win; skipped (LONG low) legs lose -> positive lift.
    features = (
        [LegFeature("BTC", "LONG", True, 10.0, 0, 0.9) for _ in range(8)]
        + [LegFeature("BTC", "LONG", False, -5.0, 0, 0.1) for _ in range(8)]
    )
    result = evaluate_rule(rule, features)
    assert result is not None
    assert result.taken == 8
    assert result.taken_win_rate == pytest.approx(1.0)
    assert result.base_win_rate == pytest.approx(0.5)
    assert result.win_rate_lift == pytest.approx(0.5)


def test_teacher_registry_roundtrip_and_resume(tmp_path):
    from atlas.investment.hyper_copytrade.basis_reconstruction import RealizedLeg
    from atlas.investment.hyper_copytrade.teacher_registry import (
        RegisteredLeg,
        TeacherRecord,
        append_teacher_record,
        iter_teacher_legs,
        load_teacher_records,
        scanned_addresses,
        teachers,
    )
    path = tmp_path / "reg.jsonl"
    # SHORT leg: entry 110, exit 100 -> +10/110 short return; stored exit_price.
    leg = RealizedLeg("XRP", "SHORT", 110, 1000, 100, 2000, 5.0, 50.0, True)
    teacher = TeacherRecord(
        address="0x" + "a" * 40,
        is_teacher=True,
        week_pnl=1234.0,
        account_value=500000.0,
        leg_count=1,
        median_hold_minutes=16.67,
        win_rate=1.0,
        legs=(RegisteredLeg.from_realized(leg),),
    )
    non_teacher = TeacherRecord(
        address="0x" + "b" * 40,
        is_teacher=False,
        week_pnl=99.0,
        account_value=200000.0,
        leg_count=0,
        median_hold_minutes=0.0,
        win_rate=0.0,
        legs=(),
    )
    append_teacher_record(path, teacher)
    append_teacher_record(path, non_teacher)

    records = load_teacher_records(path)
    assert len(records) == 2
    assert scanned_addresses(path) == {teacher.address, non_teacher.address}
    only_teachers = teachers(records)
    assert [t.address for t in only_teachers] == [teacher.address]

    # Rehydrated legs preserve PnL/direction/entry/exit for the analysis path.
    (addr, legs), = list(iter_teacher_legs(records))
    assert addr == teacher.address
    assert legs[0].direction == "SHORT"
    assert legs[0].closed_pnl == pytest.approx(50.0)
    assert legs[0].exit_price == pytest.approx(100.0)
    assert legs[0].entry_observed
    # Persisted exit price enables the cost-model short return.
    assert teacher.legs[0].short_return() == pytest.approx((110 - 100) / 110)


def test_teacher_registry_rejects_unknown_schema(tmp_path):
    import json
    from atlas.investment.hyper_copytrade.teacher_registry import load_teacher_records
    path = tmp_path / "bad.jsonl"
    path.write_text(
        json.dumps({"schema": "wrong.v9", "address": "0x1"}) + "\n",
        encoding="utf-8",
    )
    # Unparseable/unknown-schema lines are skipped, not fatal.
    assert load_teacher_records(path) == []


def test_wallet_leverage_ratio():
    state = WalletState.from_clearinghouse_state(
        ADDR_C,
        {
            "marginSummary": {
                "accountValue": "100000",
                "totalNtlPos": "920000",
                "totalMarginUsed": "0",
            },
            "assetPositions": [],
        },
    )
    assert state.leverage_ratio == pytest.approx(9.2)


def test_per_leg_sharpe_rewards_consistency_over_size():
    # Steady small wins beat one big lucky win wiped by many losses.
    steady = per_leg_sharpe([2.0, 1.0, 2.0, 1.0, 2.0, 1.0])  # mean 1.5, sd 0.5 -> 3.0
    lucky = per_leg_sharpe([10.0, -2.0, -2.0, -2.0, -2.0, -2.0])  # mean 0.0 -> 0.0
    assert steady == pytest.approx(3.0)
    assert lucky == pytest.approx(0.0)
    assert steady > lucky


def test_per_leg_sharpe_degenerate_inputs():
    assert per_leg_sharpe([5.0]) == 0.0  # too few legs
    assert per_leg_sharpe([3.0, 3.0, 3.0]) == 0.0  # zero variance


def test_rank_teachers_by_skill_orders_by_sharpe():
    ranked = rank_teachers_by_skill([
        ("0xlucky", [10.0, -2.0, -2.0, -2.0, -2.0, -2.0]),
        ("0xsteady", [2.0, 1.0, 2.0, 1.0, 2.0, 1.0]),
    ])
    assert [addr for addr, _ in ranked] == ["0xsteady", "0xlucky"]


def _teacher(address, pnls, is_teacher=True):
    legs = tuple(
        RegisteredLeg(
            coin="BTC", direction="LONG", is_win=(p > 0), closed_pnl=float(p),
            entry_price=100.0, entry_time_ms=i, exit_time_ms=i + 1,
        )
        for i, p in enumerate(pnls)
    )
    return TeacherRecord(
        address=address, is_teacher=is_teacher, week_pnl=float(sum(pnls)),
        account_value=1_000_000.0, leg_count=len(pnls), median_hold_minutes=10.0,
        win_rate=sum(1 for p in pnls if p > 0) / max(len(pnls), 1), legs=legs,
    )


def test_registry_roster_ranks_by_skill_and_filters():
    steady = _teacher("0xsteady", [2.0, 1.0] * 12)  # 24 legs, Sharpe 3.0
    lucky = _teacher("0xlucky", [10.0] + [-2.0] * 23)  # 24 legs, negative Sharpe
    too_few = _teacher("0xfew", [5.0, 1.0, 5.0, 1.0])  # 4 legs, excluded
    non_teacher = _teacher("0xnot", [3.0, 1.0] * 12, is_teacher=False)  # excluded

    roster = select_registry_roster_by_skill(
        [lucky, steady, too_few, non_teacher], size=5, minimum_legs=20
    )
    assert [m.address for m in roster] == ["0xsteady", "0xlucky"]  # skill order
    assert roster[0].per_leg_sharpe > roster[1].per_leg_sharpe
    # too_few (below minimum_legs) and non_teacher are excluded
    assert {"0xfew", "0xnot"}.isdisjoint({m.address for m in roster})


def test_registry_roster_honors_size():
    records = [_teacher(f"0x{i}", [2.0, 1.0] * 12) for i in range(5)]
    assert len(select_registry_roster_by_skill(records, size=3, minimum_legs=20)) == 3


# ---------------------------------------------------------------------------
# Forward paper runner: mids fetch + per-cycle mechanics (offline).
# ---------------------------------------------------------------------------

_FORWARD_LIMITS = RiskLimits(
    allow_short_positions=True, maximum_leverage=3.0,
    maximum_order_notional=1_000_000.0, maximum_asset_notional=1_000_000.0,
    maximum_gross_exposure=1_000_000.0, maximum_daily_loss=1_000_000.0,
)
_PRICES = {"BTC": 100.0, "XRP": 2.0}


def test_fetch_all_mids_parses_upper_cases_and_filters(monkeypatch):
    client = HyperliquidReadClient()
    monkeypatch.setattr(
        client, "_post_json",
        lambda url, body: {"BTC": "65000.5", "eth": "3200", "NAN": "nan",
                           "ZERO": "0", "JUNK": "notanumber"},
    )
    mids = client.fetch_all_mids()
    assert mids["BTC"] == pytest.approx(65000.5)
    assert mids["ETH"] == pytest.approx(3200.0)  # upper-cased key
    for dropped in ("NAN", "ZERO", "JUNK"):
        assert dropped not in mids


def test_fetch_all_mids_rejects_non_object(monkeypatch):
    client = HyperliquidReadClient()
    monkeypatch.setattr(client, "_post_json", lambda url, body: ["BTC", "100"])
    with pytest.raises(HyperliquidClientError):
        client.fetch_all_mids()


def test_forward_cycle_opens_signed_book_and_marks():
    account = AccountSnapshot(cash=100_000.0)
    targets = {"BTC": 30_000.0, "XRP": -20_000.0}
    account, fills = rebalance_to_targets(
        account, targets, _PRICES, limits=_FORWARD_LIMITS,
        minimum_rebalance_notional=50.0,
    )
    assert fills == 2
    pos = positions_map(account)
    assert pos["BTC"] > 0.0 and pos["XRP"] < 0.0  # long BTC, short XRP
    gross = sum(abs(q) * _PRICES[a] for a, q in pos.items())
    assert 49_000.0 < gross < 50_500.0  # ~50k gross, minus fill costs
    equity = net_liquidation(account, _PRICES)
    assert 99_000.0 < equity <= 100_000.0  # only fees/slippage, no phantom P&L

    # A second identical rebalance is a no-op: the book is already on target,
    # so every residual delta is dust below the minimum notional.
    _, fills_again = rebalance_to_targets(
        account, targets, _PRICES, limits=_FORWARD_LIMITS,
        minimum_rebalance_notional=50.0,
    )
    assert fills_again == 0


def test_rebalance_skips_asset_without_a_live_price():
    account = AccountSnapshot(cash=100_000.0)
    account, fills = rebalance_to_targets(
        account, {"BTC": 10_000.0, "DOGE": 5_000.0}, {"BTC": 100.0},
        limits=_FORWARD_LIMITS, minimum_rebalance_notional=50.0,
    )
    assert fills == 1  # DOGE has no price -> skipped, not closed at zero
    assert "DOGE" not in positions_map(account)


def test_accrue_funding_charges_gross_and_is_noop_on_zero_span():
    account = AccountSnapshot(cash=100_000.0)
    account, _ = rebalance_to_targets(
        account, {"BTC": 30_000.0, "XRP": -20_000.0}, _PRICES,
        limits=_FORWARD_LIMITS, minimum_rebalance_notional=50.0,
    )
    gross = sum(abs(q) * _PRICES[a] for a, q in positions_map(account).items())
    charged, paid = accrue_funding(
        account, _PRICES, elapsed_days=2.0, funding_bps_per_day=3.0
    )
    assert paid == pytest.approx(3.0 / 10_000.0 * 2.0 * gross, rel=1e-9)
    assert charged.cash == pytest.approx(account.cash - paid)

    same, paid_zero = accrue_funding(
        account, _PRICES, elapsed_days=0.0, funding_bps_per_day=3.0
    )
    assert paid_zero == 0.0
    assert same is account  # same-cycle re-run does not double-charge


def test_target_notionals_projects_book_signs():
    state = WalletState.from_clearinghouse_state(
        ADDR_C,
        _clearinghouse("600000", [
            _asset_position("BTC", "6000", 5),   # long
            _asset_position("XRP", "-4000", 5),  # short
        ]),
    )
    book = blend_targets([state], paper_capital=100_000.0)
    projected = target_notionals(book)
    assert set(projected) == {"BTC", "XRP"}
    assert projected["BTC"] > 0.0 and projected["XRP"] < 0.0


def test_tradable_perp_coins_are_short_enabled_registered_majors():
    universe = tradable_perp_coins()
    for major in ("BTC", "ETH", "SOL", "XRP", "AAVE"):
        assert major in universe  # aliased, short-enabled perps
    assert "HYPE" not in universe  # unregistered alt: not mirrorable
    assert "GOLD" not in universe and "GLD" not in universe  # spot ETF, no short


def test_restrict_states_drops_untradable_coins_and_reports_coverage():
    state = WalletState.from_clearinghouse_state(
        ADDR_C,
        _clearinghouse("600000", [
            _asset_position("BTC", "100", 5),    # positionValue 10,000 (tradable)
            _asset_position("HYPE", "50", 5),    # positionValue  5,000 (untradable)
        ]),
    )
    filtered, coverage = restrict_states_to_universe([state], tradable_perp_coins())
    assert len(filtered) == 1
    assert {p.coin for p in filtered[0].positions} == {"BTC"}  # HYPE removed
    assert coverage.dropped_coins == ("HYPE",)
    assert coverage.coverage_fraction == pytest.approx(10_000.0 / 15_000.0)
    # equity preserved -> the tradable slice keeps its fraction-of-equity sizing
    assert filtered[0].account_value == pytest.approx(600_000.0)


def test_restrict_drops_wallet_with_no_tradable_positions():
    state = WalletState.from_clearinghouse_state(
        ADDR_B,
        _clearinghouse("100000", [_asset_position("HYPE", "50", 5)]),
    )
    filtered, coverage = restrict_states_to_universe([state], tradable_perp_coins())
    assert filtered == []  # nothing tradable -> wallet contributes nothing
    assert coverage.coverage_fraction == pytest.approx(0.0)
    assert coverage.dropped_coins == ("HYPE",)


def test_fit_targets_to_cash_scales_net_long_book_to_fit_equity():
    # All-long book of 150k net on 100k equity: not fundable cash-settled.
    targets = {"BTC": 60_000.0, "ETH": 50_000.0, "SOL": 40_000.0}  # net long 150k
    fitted, scale = fit_targets_to_cash(targets, 100_000.0, fee_buffer_bps=0.0)
    assert scale == pytest.approx(100_000.0 / 150_000.0)
    net_long = sum(fitted.values())
    assert net_long == pytest.approx(100_000.0)  # lands exactly on equity


def test_fit_targets_to_cash_leaves_hedged_book_untouched():
    # Gross 5x but net long only 0.5x on 100k: shorts fund the longs, fundable.
    targets = {"BTC": 300_000.0, "ETH": -250_000.0}  # gross 550k, net long 50k
    fitted, scale = fit_targets_to_cash(targets, 100_000.0)
    assert scale == 1.0
    assert fitted == targets  # unchanged: net long already inside equity


def test_fit_targets_to_cash_leaves_net_short_book_untouched():
    targets = {"BTC": 20_000.0, "ETH": -90_000.0}  # net short
    fitted, scale = fit_targets_to_cash(targets, 100_000.0)
    assert scale == 1.0
    assert fitted == targets


def test_rebalance_frees_cash_before_spending_it_on_full_rotation():
    # A near-fully-deployed long book rotated into a different coin only fully
    # fills if the sell settles before the buy draws cash -- the cash-settled
    # ordering guarantee. Without sells-first, the buy would trip INSUFFICIENT_CASH.
    prices = {"BTC": 100.0, "ETH": 100.0}
    account = AccountSnapshot(cash=100_000.0)
    account, _ = rebalance_to_targets(
        account, {"BTC": 95_000.0}, prices, limits=_FORWARD_LIMITS,
        minimum_rebalance_notional=50.0,
    )
    assert positions_map(account)["BTC"] > 0.0  # deployed into BTC

    account, fills = rebalance_to_targets(
        account, {"ETH": 95_000.0}, prices, limits=_FORWARD_LIMITS,
        minimum_rebalance_notional=50.0,
    )
    pos = positions_map(account)
    assert fills == 2  # BTC fully sold AND ETH fully bought
    assert pos.get("ETH", 0.0) > 0.0
    assert abs(pos.get("BTC", 0.0)) < 1e-6  # rotated out of BTC entirely
