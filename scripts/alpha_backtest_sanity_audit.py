
"""Alpha Backtest Sanity Audit.

Checks:
- return scale / outliers
- duplicate trades
- overlapping trades
- asset concentration
- top/worst trades
- non-overlapping sample performance

Reads:
- output/investment_alpha/alpha_backtest_trades.csv
- output/investment_alpha/alpha_rankings.csv

Writes:
- output/investment_alpha/alpha_backtest_sanity_audit.json
- output/investment_alpha/alpha_backtest_sanity_audit.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


OUT_DIR = Path("output/investment_alpha")
TRADES_CSV = OUT_DIR / "alpha_backtest_trades.csv"
RANKINGS_CSV = OUT_DIR / "alpha_rankings.csv"
JSON_PATH = OUT_DIR / "alpha_backtest_sanity_audit.json"
MD_PATH = OUT_DIR / "alpha_backtest_sanity_audit.md"


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def summarize_returns(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty or "return" not in df.columns:
        return {"count": 0}

    s = pd.to_numeric(df["return"], errors="coerce").dropna()
    if s.empty:
        return {"count": 0}

    return {
        "count": int(s.count()),
        "win_rate": round(float((s > 0).mean()), 6),
        "mean": round(float(s.mean()), 8),
        "median": round(float(s.median()), 8),
        "std": round(float(s.std()), 8),
        "min": round(float(s.min()), 8),
        "max": round(float(s.max()), 8),
        "p01": round(float(s.quantile(0.01)), 8),
        "p05": round(float(s.quantile(0.05)), 8),
        "p95": round(float(s.quantile(0.95)), 8),
        "p99": round(float(s.quantile(0.99)), 8),
        "gt_100pct_count": int((s > 1.0).sum()),
        "gt_500pct_count": int((s > 5.0).sum()),
        "lt_minus_80pct_count": int((s < -0.80).sum()),
    }


def by_hypothesis(trades: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []

    for hypothesis_id, group in trades.groupby("hypothesis_id"):
        summary = summarize_returns(group)
        assets = group["asset"].value_counts(dropna=False).to_dict() if "asset" in group.columns else {}

        rows.append(
            {
                "hypothesis_id": hypothesis_id,
                "summary": summary,
                "asset_counts": {str(k): int(v) for k, v in assets.items()},
                "duplicate_trades": count_duplicate_trades(group),
                "non_overlapping_summary": summarize_returns(non_overlapping(group)),
            }
        )

    return sorted(rows, key=lambda x: x["summary"].get("mean") or -999, reverse=True)


def count_duplicate_trades(df: pd.DataFrame) -> int:
    needed = ["hypothesis_id", "date", "asset", "hold_period"]
    if not all(col in df.columns for col in needed):
        return 0
    return int(df.duplicated(subset=needed).sum())


def non_overlapping(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or not {"date", "asset", "hold_period"}.issubset(df.columns):
        return df

    out_rows = []
    tmp = df.copy()
    tmp["date"] = pd.to_datetime(tmp["date"], errors="coerce")
    tmp = tmp.dropna(subset=["date"]).sort_values(["asset", "date"])

    for asset, group in tmp.groupby("asset"):
        next_allowed = None

        for _, row in group.iterrows():
            date = row["date"]
            hold = int(row.get("hold_period") or 0)

            if next_allowed is None or date >= next_allowed:
                out_rows.append(row)
                next_allowed = date + pd.Timedelta(hours=hold)

    return pd.DataFrame(out_rows)


def top_worst_trades(trades: pd.DataFrame, n: int = 20) -> dict[str, list[dict[str, Any]]]:
    if trades.empty or "return" not in trades.columns:
        return {"top": [], "worst": []}

    tmp = trades.copy()
    tmp["return"] = pd.to_numeric(tmp["return"], errors="coerce")
    tmp = tmp.dropna(subset=["return"])

    cols = [
        col for col in [
            "hypothesis_id",
            "family",
            "date",
            "asset",
            "direction",
            "hold_period",
            "return",
        ]
        if col in tmp.columns
    ]

    return {
        "top": tmp.sort_values("return", ascending=False).head(n)[cols].to_dict("records"),
        "worst": tmp.sort_values("return", ascending=True).head(n)[cols].to_dict("records"),
    }


def build_warnings(report: dict[str, Any]) -> list[str]:
    warnings = []

    overall = report.get("overall", {})
    if overall.get("max", 0) > 10:
        warnings.append("Extreme positive return above 1000% detected. Verify return scale and data integrity.")

    if overall.get("mean", 0) > 1:
        warnings.append("Average return above 100% detected. Validate whether returns are decimal-scaled and not shifted incorrectly.")

    if report.get("duplicate_trades", 0) > 0:
        warnings.append(f"Duplicate trades detected: {report.get('duplicate_trades')}.")

    for item in report.get("by_hypothesis", []):
        h = item.get("hypothesis_id")
        s = item.get("summary", {})
        non = item.get("non_overlapping_summary", {})

        if s.get("count", 0) >= 20 and non.get("count", 0) < max(5, s.get("count", 0) * 0.1):
            warnings.append(f"{h}: non-overlapping trade count is very small versus raw count.")

        asset_counts = item.get("asset_counts", {})
        total = sum(asset_counts.values())
        if total:
            largest_asset, largest_count = max(asset_counts.items(), key=lambda kv: kv[1])
            if largest_count / total > 0.80:
                warnings.append(f"{h}: performance sample is highly concentrated in {largest_asset}.")

    return warnings


def build_sanity_audit() -> dict[str, Any]:
    trades = load_csv(TRADES_CSV)
    rankings = load_csv(RANKINGS_CSV)

    if trades.empty:
        report = {
            "success": False,
            "error": f"Missing or empty trades file: {TRADES_CSV}",
        }
        write_outputs(report)
        return report

    duplicate_trades = count_duplicate_trades(trades)
    overall = summarize_returns(trades)
    non_overlap = summarize_returns(non_overlapping(trades))
    hypothesis = by_hypothesis(trades)
    extremes = top_worst_trades(trades)

    report = {
        "success": True,
        "trades_path": str(TRADES_CSV),
        "rankings_path": str(RANKINGS_CSV),
        "trade_rows": int(len(trades)),
        "ranking_rows": int(len(rankings)),
        "duplicate_trades": duplicate_trades,
        "overall": overall,
        "non_overlapping_overall": non_overlap,
        "by_hypothesis": hypothesis,
        "extreme_trades": extremes,
        "summary": (
            f"Alpha sanity audit scanned {len(trades)} trade row(s) "
            f"across {trades['hypothesis_id'].nunique() if 'hypothesis_id' in trades.columns else 0} hypothesis/hypotheses."
        ),
    }

    report["warnings"] = build_warnings(report)
    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    MD_PATH.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Alpha Backtest Sanity Audit",
        "",
        report.get("summary", report.get("error", "")),
        "",
        "## Warnings",
        "",
    ]

    warnings = report.get("warnings", []) or []
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- No warnings.")

    overall = report.get("overall", {}) or {}
    non = report.get("non_overlapping_overall", {}) or {}

    lines.extend([
        "",
        "## Overall",
        "",
        f"- Trades: `{overall.get('count')}`",
        f"- Win rate: `{overall.get('win_rate')}`",
        f"- Mean: `{overall.get('mean')}`",
        f"- Median: `{overall.get('median')}`",
        f"- Min: `{overall.get('min')}`",
        f"- Max: `{overall.get('max')}`",
        f"- >100% count: `{overall.get('gt_100pct_count')}`",
        f"- >500% count: `{overall.get('gt_500pct_count')}`",
        "",
        "## Non-Overlapping Overall",
        "",
        f"- Trades: `{non.get('count')}`",
        f"- Win rate: `{non.get('win_rate')}`",
        f"- Mean: `{non.get('mean')}`",
        f"- Median: `{non.get('median')}`",
        f"- Min: `{non.get('min')}`",
        f"- Max: `{non.get('max')}`",
        "",
        "## Top Hypothesis Sanity",
        "",
    ])

    for item in (report.get("by_hypothesis", []) or [])[:20]:
        s = item.get("summary", {}) or {}
        ns = item.get("non_overlapping_summary", {}) or {}

        lines.extend([
            f"### {item.get('hypothesis_id')}",
            "",
            f"- Trades: `{s.get('count')}`",
            f"- Win rate: `{s.get('win_rate')}`",
            f"- Mean: `{s.get('mean')}`",
            f"- Median: `{s.get('median')}`",
            f"- Min: `{s.get('min')}`",
            f"- Max: `{s.get('max')}`",
            f"- Non-overlap trades: `{ns.get('count')}`",
            f"- Non-overlap mean: `{ns.get('mean')}`",
            f"- Duplicate trades: `{item.get('duplicate_trades')}`",
            f"- Asset counts: `{item.get('asset_counts')}`",
            "",
        ])

    lines.extend(["## Extreme Top Trades", ""])

    for row in (report.get("extreme_trades", {}) or {}).get("top", [])[:10]:
        lines.append(f"- `{row}`")

    lines.extend(["", "## Extreme Worst Trades", ""])

    for row in (report.get("extreme_trades", {}) or {}).get("worst", [])[:10]:
        lines.append(f"- `{row}`")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = build_sanity_audit()
    print(report["success"])
    print(report.get("summary", report.get("error", "")))
    print("Warnings:", len(report.get("warnings", [])))
    for warning in report.get("warnings", [])[:20]:
        print("-", warning)
    print(f"JSON: {JSON_PATH}")
    print(f"Markdown: {MD_PATH}")


if __name__ == "__main__":
    main()
