
"""Market Universe v1 liquidity and data-quality gates."""

from __future__ import annotations

from datetime import datetime, UTC

import pandas as pd


def evaluate_market_universe(
    prices: pd.DataFrame,
    config: dict,
    fetch_errors: list[dict],
) -> list[dict]:
    gates = config.get("liquidity_gates", {}) or {}
    required = set(
        config.get("required_core_assets", []) or []
    )
    metadata = {
        str(row.get("asset")): row
        for row in config.get("whitelist", [])
        if row.get("asset")
    }

    fetch_error_map = {
        str(row.get("asset")): row
        for row in fetch_errors
    }

    rows = []

    for asset, meta in metadata.items():
        asset_frame = (
            prices[prices["asset"].astype(str) == asset].copy()
            if prices is not None
            and not prices.empty
            and "asset" in prices.columns
            else pd.DataFrame()
        )

        metrics = calculate_metrics(asset_frame)
        failures = evaluate_failures(
            metrics,
            gates,
            fetch_error_map.get(asset),
        )

        required_core = asset in required
        approved = len(failures) == 0

        if required_core and not approved:
            status = "REQUIRED_CORE_FAILED"
        elif approved:
            status = "APPROVED"
        else:
            status = "REJECTED"

        rows.append({
            "asset": asset,
            "tier": meta.get("tier", "UNKNOWN"),
            "sector": meta.get("sector", "unknown"),
            "required_core": required_core,
            "enabled": bool(meta.get("enabled", False)),
            "approved": approved,
            "status": status,
            "observation_count": metrics["observation_count"],
            "latest_timestamp": metrics["latest_timestamp"],
            "stale_days": metrics["stale_days"],
            "latest_close": metrics["latest_close"],
            "missing_close_ratio": metrics[
                "missing_close_ratio"
            ],
            "average_daily_dollar_volume": metrics[
                "average_daily_dollar_volume"
            ],
            "median_daily_dollar_volume": metrics[
                "median_daily_dollar_volume"
            ],
            "failure_reasons": failures,
            "source": "market_universe_v1",
        })

    return rows


def calculate_metrics(frame: pd.DataFrame) -> dict:
    if frame is None or frame.empty:
        return {
            "observation_count": 0,
            "latest_timestamp": None,
            "stale_days": None,
            "latest_close": 0.0,
            "missing_close_ratio": 1.0,
            "average_daily_dollar_volume": 0.0,
            "median_daily_dollar_volume": 0.0,
        }

    timestamps = pd.to_datetime(
        frame["timestamp"],
        errors="coerce",
        utc=True,
    )
    closes = pd.to_numeric(
        frame["close"],
        errors="coerce",
    )
    dollar_volume = pd.to_numeric(
        frame["dollar_volume"],
        errors="coerce",
    )

    valid_timestamps = timestamps.dropna()
    latest_timestamp = (
        valid_timestamps.max()
        if not valid_timestamps.empty
        else None
    )

    now = pd.Timestamp(datetime.now(UTC))
    stale_days = (
        int((now - latest_timestamp).total_seconds() // 86400)
        if latest_timestamp is not None
        else None
    )

    valid_closes = closes.dropna()

    return {
        "observation_count": int(len(frame)),
        "latest_timestamp": (
            latest_timestamp.isoformat()
            if latest_timestamp is not None
            else None
        ),
        "stale_days": stale_days,
        "latest_close": (
            float(valid_closes.iloc[-1])
            if not valid_closes.empty
            else 0.0
        ),
        "missing_close_ratio": round(
            float(closes.isna().mean()),
            6,
        ),
        "average_daily_dollar_volume": round(
            float(dollar_volume.dropna().mean())
            if not dollar_volume.dropna().empty
            else 0.0,
            2,
        ),
        "median_daily_dollar_volume": round(
            float(dollar_volume.dropna().median())
            if not dollar_volume.dropna().empty
            else 0.0,
            2,
        ),
    }


def evaluate_failures(
    metrics: dict,
    gates: dict,
    fetch_error: dict | None,
) -> list[str]:
    failures = []

    if fetch_error:
        failures.append(
            f"fetch_error:{fetch_error.get('error_type')}"
        )

    if metrics["observation_count"] < int(
        gates.get("minimum_observations", 0)
    ):
        failures.append("insufficient_observations")

    if metrics["latest_close"] < float(
        gates.get("minimum_price", 0.0)
    ):
        failures.append("price_below_minimum")

    if metrics["median_daily_dollar_volume"] < float(
        gates.get(
            "minimum_median_daily_dollar_volume",
            0.0,
        )
    ):
        failures.append(
            "median_dollar_volume_below_minimum"
        )

    if metrics["average_daily_dollar_volume"] < float(
        gates.get(
            "minimum_average_daily_dollar_volume",
            0.0,
        )
    ):
        failures.append(
            "average_dollar_volume_below_minimum"
        )

    stale_days = metrics.get("stale_days")

    if (
        stale_days is None
        or stale_days
        > int(gates.get("maximum_stale_days", 999999))
    ):
        failures.append("stale_market_data")

    if metrics["missing_close_ratio"] > float(
        gates.get("maximum_missing_close_ratio", 1.0)
    ):
        failures.append("excessive_missing_close_data")

    return failures
