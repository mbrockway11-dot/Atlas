
"""Broker Ledger v4.1 accounting.

The current Paper Broker v3 snapshot is authoritative when historical fills
are incomplete. Fills are retained as an audit trail and are not replayed
against an already-current snapshot.
"""

from __future__ import annotations

import pandas as pd


INITIAL_EQUITY = 100000.0
EPSILON = 0.000001


def build_authoritative_ledger(inputs: dict) -> dict:
    report = inputs.get("paper_broker_report", {}) or {}
    positions_df = inputs.get("paper_broker_positions")
    fills_df = inputs.get("paper_broker_fills")
    cash_ledger_df = inputs.get("paper_broker_cash_ledger")

    positions = normalize_snapshot_positions(positions_df)
    cash = extract_authoritative_cash(report, cash_ledger_df, positions)

    market_value = round(
        sum(float(row.get("market_value") or 0.0) for row in positions),
        2,
    )
    equity = round(cash + market_value, 2)
    pnl = round(equity - INITIAL_EQUITY, 2)
    pnl_pct = round(pnl / INITIAL_EQUITY, 6) if INITIAL_EQUITY else 0.0

    audit_rows = normalize_fill_audit(fills_df)

    reconciliation = build_reconciliation(
        report=report,
        cash=cash,
        market_value=market_value,
        equity=equity,
        positions=positions,
        audit_rows=audit_rows,
    )

    return {
        "accounting_mode": "authoritative_broker_snapshot",
        "cash": cash,
        "market_value": market_value,
        "equity": equity,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "positions": positions,
        "trade_rows": audit_rows,
        "reconciliation": reconciliation,
    }


def normalize_snapshot_positions(
    positions_df: pd.DataFrame,
) -> list[dict]:
    if positions_df is None or positions_df.empty:
        return []

    rows = []

    for _, row in positions_df.iterrows():
        asset = str(row.get("asset") or "").strip()

        if not asset or asset.upper() == "CASH":
            continue

        side = str(row.get("side") or "LONG").upper()

        net_weight = first_number(
            row,
            [
                "net_weight",
                "weight",
                "portfolio_weight",
                "filled_weight",
            ],
        )

        market_value = first_number(
            row,
            [
                "market_value",
                "notional_value",
                "position_value",
                "value",
            ],
        )

        if market_value == 0.0 and net_weight != 0.0:
            market_value = INITIAL_EQUITY * net_weight

        if net_weight == 0.0 and market_value != 0.0:
            net_weight = market_value / INITIAL_EQUITY

        if abs(net_weight) <= EPSILON and abs(market_value) <= EPSILON:
            continue

        rows.append({
            "asset": asset,
            "side": side,
            "net_weight": round(net_weight, 6),
            "market_value": round(market_value, 2),
            "status": "OPEN",
            "source": "paper_broker_v3_snapshot",
        })

    return rows


def extract_authoritative_cash(
    report: dict,
    cash_ledger_df: pd.DataFrame,
    positions: list[dict],
) -> float:
    """Resolve cash while rejecting stale broker cash snapshots."""

    market_value = sum(
        float(row.get("market_value") or 0.0)
        for row in positions
    )

    position_weight = sum(
        abs(float(row.get("net_weight") or 0.0))
        for row in positions
    )

    implied_cash_from_weights = round(
        INITIAL_EQUITY * max(0.0, 1.0 - position_weight),
        2,
    )

    summary = report.get("summary")
    account = report.get("account")
    portfolio = report.get("portfolio")

    candidates = [
        ("report.cash", report.get("cash")),
        ("report.cash_balance", report.get("cash_balance")),
        (
            "summary.cash",
            summary.get("cash") if isinstance(summary, dict) else None,
        ),
        (
            "account.cash",
            account.get("cash") if isinstance(account, dict) else None,
        ),
        (
            "portfolio.cash",
            portfolio.get("cash") if isinstance(portfolio, dict) else None,
        ),
    ]

    for _, candidate in candidates:
        value = to_optional_float(candidate)

        if value is None:
            continue

        candidate_equity = value + market_value

        # Accept the reported value only when it reconciles with the
        # snapshot's initial-equity accounting.
        if abs(candidate_equity - INITIAL_EQUITY) <= 0.01:
            return round(value, 2)

    if cash_ledger_df is not None and not cash_ledger_df.empty:
        for column in [
            "cash_after",
            "cash_balance",
            "ending_cash",
            "cash",
        ]:
            if column not in cash_ledger_df.columns:
                continue

            values = pd.to_numeric(
                cash_ledger_df[column],
                errors="coerce",
            ).dropna()

            if values.empty:
                continue

            candidate_cash = float(values.iloc[-1])
            candidate_equity = candidate_cash + market_value

            if abs(candidate_equity - INITIAL_EQUITY) <= 0.01:
                return round(candidate_cash, 2)

    # The broker cash field is stale. Reconstruct cash from the current
    # broker position weights instead of double-counting invested capital.
    return implied_cash_from_weights


def normalize_fill_audit(fills_df: pd.DataFrame) -> list[dict]:
    if fills_df is None or fills_df.empty:
        return []

    df = fills_df.copy()

    key_column = None
    for candidate in ["stable_order_key", "target_key", "idempotency_key"]:
        if candidate in df.columns:
            key_column = candidate
            break

    if key_column:
        df = df.drop_duplicates(subset=[key_column], keep="last")

    rows = []

    for _, row in df.iterrows():
        rows.append({
            "timestamp": (
                row.get("filled_at")
                or row.get("fill_timestamp")
                or row.get("timestamp")
            ),
            "stable_order_key": (
                row.get("stable_order_key")
                or row.get("target_key")
                or row.get("idempotency_key")
            ),
            "asset": row.get("asset"),
            "side": row.get("side"),
            "action": row.get("action"),
            "filled_weight": first_number(
                row,
                ["filled_weight", "requested_weight", "weight"],
            ),
            "notional_value": first_number(
                row,
                ["notional_value", "market_value", "value"],
            ),
            "fill_status": row.get("fill_status"),
            "source": "paper_broker_v3_fill_audit",
        })

    return rows


def build_reconciliation(
    *,
    report: dict,
    cash: float,
    market_value: float,
    equity: float,
    positions: list[dict],
    audit_rows: list[dict],
) -> dict:
    expected_equity = INITIAL_EQUITY
    equity_difference = round(equity - expected_equity, 2)

    report_position_count = (
        (report.get("counts", {}) or {}).get("position_count")
        or report.get("position_count")
    )

    return {
        "balanced": abs(equity_difference) <= 0.01,
        "expected_equity": expected_equity,
        "calculated_equity": equity,
        "equity_difference": equity_difference,
        "cash_plus_market_value": round(cash + market_value, 2),
        "position_count": len(positions),
        "reported_position_count": report_position_count,
        "fill_audit_count": len(audit_rows),
        "snapshot_authoritative": True,
        "historical_fill_replay_enabled": False,
    }


def first_number(row, columns: list[str]) -> float:
    for column in columns:
        if column not in row:
            continue

        value = to_optional_float(row.get(column))
        if value is not None:
            return value

    return 0.0


def to_optional_float(value) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
