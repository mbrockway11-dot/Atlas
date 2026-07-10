
"""Alpha Backtesting report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

REGIME_JSON = Path("output/investment_regime/investment_regime_validation.json")

from atlas.investment.alpha.backtester.engine import run_alpha_backtests


OUT_DIR = Path("output/investment_alpha")
RESULTS_JSON = OUT_DIR / "alpha_backtests.json"
RANKINGS_CSV = OUT_DIR / "alpha_rankings.csv"
TRADES_CSV = OUT_DIR / "alpha_backtest_trades.csv"
REPORT_MD = OUT_DIR / "alpha_backtest_report.md"



def attach_regime_labels(trades: pd.DataFrame) -> pd.DataFrame:
    """Attach derived regime labels to alpha trade rows."""
    if trades.empty:
        return trades

    market_features_path = Path("output/investment_alpha/market_features.csv")
    if not market_features_path.exists():
        return trades

    market = pd.read_csv(market_features_path)
    if "date" not in market.columns:
        return trades

    market["date"] = pd.to_datetime(market["date"], errors="coerce")

    if "trend_regime" not in market.columns:
        if "median_return_288" in market.columns:
            market["trend_regime"] = market["median_return_288"].apply(classify_trend_regime)
        elif "mean_return_288" in market.columns:
            market["trend_regime"] = market["mean_return_288"].apply(classify_trend_regime)

    if "volatility_regime" not in market.columns:
        if "dispersion_72" in market.columns:
            cutoff = pd.to_numeric(market["dispersion_72"], errors="coerce").median()
            market["volatility_regime"] = market["dispersion_72"].apply(
                lambda x: classify_volatility_regime(x, cutoff)
            )

    if "topology_regime" not in market.columns and "graph_density" in market.columns:
        cutoff = pd.to_numeric(market["graph_density"], errors="coerce").median()
        market["topology_regime"] = market["graph_density"].apply(
            lambda x: "high_density" if pd.notna(x) and x >= cutoff else "low_density"
        )

    regime_cols = [
        col for col in [
            "date",
            "trend_regime",
            "volatility_regime",
            "topology_regime",
            "leadership_asset",
            "graph_density",
            "avg_abs_corr",
            "leader_asset_72",
            "leader_laggard_spread_72",
        ]
        if col in market.columns
    ]

    out = trades.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")

    return out.merge(
        market[regime_cols].drop_duplicates(subset=["date"]),
        on="date",
        how="left",
    )


def classify_trend_regime(value) -> str:
    try:
        x = float(value)
    except Exception:
        return "unknown"

    if x > 0.08:
        return "bull"
    if x < -0.08:
        return "bear"
    return "sideways"


def classify_volatility_regime(value, cutoff) -> str:
    try:
        x = float(value)
        c = float(cutoff)
    except Exception:
        return "unknown"

    return "high_volatility" if x >= c else "low_volatility"

def build_alpha_backtest_report(min_trades: int = 5) -> dict[str, Any]:

    """Build and export alpha backtest report."""
    result = run_alpha_backtests(min_trades=min_trades)
    trades: pd.DataFrame = result.pop("trades")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    RESULTS_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    rankings = flatten_rankings(result.get("ranked_results", []))
    rankings.to_csv(RANKINGS_CSV, index=False)

    trades = attach_regime_labels(trades)

    if not trades.empty:
        trades.to_csv(TRADES_CSV, index=False)
    else:
        pd.DataFrame().to_csv(TRADES_CSV, index=False)

    REPORT_MD.write_text(build_markdown(result), encoding="utf-8")

    result["json_path"] = str(RESULTS_JSON)
    result["rankings_csv"] = str(RANKINGS_CSV)
    result["trades_csv"] = str(TRADES_CSV)
    result["markdown_path"] = str(REPORT_MD)

    return result


def flatten_rankings(results: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []

    for row in results:
        metrics = row.get("metrics", {}) or {}
        flat = {
            "hypothesis_id": row.get("hypothesis_id"),
            "family": row.get("family"),
            "alpha_score": row.get("alpha_score"),
            "passed_min_trades": row.get("passed_min_trades"),
            "description": row.get("description"),
            "signal_asset_rule": row.get("signal_asset_rule"),
            "hold_period": row.get("hold_period"),
            "direction": row.get("direction"),
        }
        flat.update({f"raw_{k}": v for k, v in metrics.items()})

        non_metrics = row.get("non_overlapping_metrics", {}) or {}
        flat.update({f"non_overlap_{k}": v for k, v in non_metrics.items()})

        flat["asset_concentration"] = row.get("asset_concentration")
        flat["asset_counts"] = row.get("asset_counts")

        rows.append(flat)

    return pd.DataFrame(rows)


def build_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Alpha Backtest Report",
        "",
        result.get("summary", ""),
        "",
        f"- Hypotheses evaluated: `{result.get('result_count')}`",
        f"- Minimum trades threshold: `{result.get('min_trades')}`",
        "",
        "## Top 10",
        "",
    ]

    for row in (result.get("ranked_results", []) or [])[:10]:
        m = row.get("metrics", {}) or {}
        lines.extend([
            f"### {row.get('hypothesis_id')}",
            "",
            f"- Family: `{row.get('family')}`",
            f"- Alpha score: `{row.get('alpha_score')}`",
            f"- Raw trades: `{m.get('trade_count')}`",
            f"- Raw win rate: `{m.get('win_rate')}`",
            f"- Raw avg return: `{m.get('avg_return')}`",
            f"- Raw total return: `{m.get('total_return')}`",
            f"- Raw max drawdown: `{m.get('max_drawdown')}`",
            f"- Raw profit factor: `{m.get('profit_factor')}`",
            f"- Non-overlap metrics: `{row.get('non_overlapping_metrics')}`",
            f"- Asset concentration: `{row.get('asset_concentration')}`",
            "",
            row.get("description", ""),
            "",
        ])

    return "\n".join(lines)
