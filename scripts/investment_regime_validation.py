
"""Investment Regime Validation.

Segments investment outcomes by:
- bull / bear / sideways regime
- high / low volatility regime
- asset leadership regime
- drawdown regime

Outputs:
- output/investment_regime/investment_regime_validation.json
- output/investment_regime/investment_regime_validation.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_ROOT = Path(r"C:\Users\lyfe1\OneDrive\Desktop\sigil-engine")
OUT_DIR = Path("output/investment_regime")
JSON_PATH = OUT_DIR / "investment_regime_validation.json"
MD_PATH = OUT_DIR / "investment_regime_validation.md"


def resolve(root: Path, relative: str) -> Path:
    return root / relative


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def detect_date_col(df: pd.DataFrame) -> str:
    for col in ["date", "timestamp", "datetime", "entry_time", "session_date"]:
        if col in df.columns:
            return col
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            return col
    return ""


def detect_asset_col(df: pd.DataFrame) -> str:
    for col in ["asset", "symbol", "leader_asset", "trade_asset"]:
        if col in df.columns:
            return col
    for col in df.columns:
        if "asset" in col.lower() or "symbol" in col.lower():
            return col
    return ""


def normalize_price_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    date_col = detect_date_col(df)
    asset_col = detect_asset_col(df)

    if not date_col or not asset_col or "close" not in df.columns:
        return pd.DataFrame()

    out = df[[date_col, asset_col, "close"]].copy()
    out.columns = ["date", "asset", "close"]
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out = out.dropna(subset=["date", "asset", "close"])
    out = out.sort_values(["asset", "date"])

    out["return_1"] = out.groupby("asset")["close"].pct_change()
    out["return_24"] = out.groupby("asset")["close"].pct_change(24)
    out["return_72"] = out.groupby("asset")["close"].pct_change(72)
    out["rolling_vol_72"] = out.groupby("asset")["return_1"].rolling(72).std().reset_index(level=0, drop=True)
    out["rolling_return_288"] = out.groupby("asset")["close"].pct_change(288)

    return out


def classify_regimes(price: pd.DataFrame) -> pd.DataFrame:
    if price.empty:
        return price

    out = price.copy()

    vol_cut = out["rolling_vol_72"].median(skipna=True)

    def trend_label(x):
        if pd.isna(x):
            return "unknown"
        if x > 0.08:
            return "bull"
        if x < -0.08:
            return "bear"
        return "sideways"

    def vol_label(x):
        if pd.isna(x):
            return "unknown"
        return "high_volatility" if x >= vol_cut else "low_volatility"

    out["trend_regime"] = out["rolling_return_288"].apply(trend_label)
    out["volatility_regime"] = out["rolling_vol_72"].apply(vol_label)

    daily = out.pivot_table(index="date", columns="asset", values="return_24")
    leader = daily.idxmax(axis=1).rename("leadership_asset")
    out = out.merge(leader, left_on="date", right_index=True, how="left")

    out["drawdown"] = out.groupby("asset")["close"].transform(lambda s: s / s.cummax() - 1)

    def dd_label(x):
        if pd.isna(x):
            return "unknown"
        if x <= -0.30:
            return "deep_drawdown"
        if x <= -0.15:
            return "moderate_drawdown"
        return "normal_drawdown"

    out["drawdown_regime"] = out["drawdown"].apply(dd_label)

    return out


def load_outcomes(root: Path) -> pd.DataFrame:
    preferred = [
        "output/backfilled_live_signals_v5.csv",
        "output/forward_outcomes.csv",
        "output/pre_signal_candidates_excess.csv",
        "output/pre_signal_candidates_v5.csv",
    ]

    for rel in preferred:
        path = resolve(root, rel)
        df = read_csv(path)
        if not df.empty:
            df["_source_file"] = rel
            return df

    return pd.DataFrame()


def normalize_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    date_col = detect_date_col(df)
    asset_col = detect_asset_col(df)

    if not date_col:
        return pd.DataFrame()

    out = df.copy()
    out["date"] = pd.to_datetime(out[date_col], errors="coerce")

    if asset_col:
        out["asset"] = out[asset_col].astype(str)
    else:
        out["asset"] = "UNKNOWN"

    return_cols = [
        col for col in out.columns
        if any(token in col.lower() for token in ["fwd_return", "forward_return", "return_hold"])
    ]

    if not return_cols:
        numeric_cols = out.select_dtypes(include="number").columns.tolist()
        return_cols = [col for col in numeric_cols if "return" in col.lower() or "ret" in col.lower()]

    out["_return_columns"] = ",".join(return_cols)
    return out.dropna(subset=["date"])


def join_regimes(outcomes: pd.DataFrame, regimes: pd.DataFrame) -> pd.DataFrame:
    if outcomes.empty or regimes.empty:
        return pd.DataFrame()

    regime_cols = [
        "date",
        "asset",
        "trend_regime",
        "volatility_regime",
        "leadership_asset",
        "drawdown_regime",
        "drawdown",
        "rolling_vol_72",
        "rolling_return_288",
    ]

    compact = regimes[regime_cols].drop_duplicates(subset=["date", "asset"])

    joined = outcomes.merge(
        compact,
        on=["date", "asset"],
        how="left",
    )

    missing = joined["trend_regime"].isna()
    if missing.any():
        market_regime = (
            regimes.sort_values("date")
            .groupby("date")[["trend_regime", "volatility_regime", "leadership_asset"]]
            .first()
            .reset_index()
        )

        joined = joined.merge(
            market_regime,
            on="date",
            how="left",
            suffixes=("", "_market"),
        )

        for col in ["trend_regime", "volatility_regime", "leadership_asset"]:
            joined[col] = joined[col].fillna(joined[f"{col}_market"])
            joined = joined.drop(columns=[f"{col}_market"])

    return joined


def summarize_returns(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"success": False, "error": "No joined outcome/regime data."}

    return_cols = []
    for col in df.columns:
        if any(token in col.lower() for token in ["fwd_return", "forward_return", "return_hold"]):
            if pd.api.types.is_numeric_dtype(df[col]):
                return_cols.append(col)

    summaries = {}

    for col in return_cols[:20]:
        summaries[col] = {
            "overall": summarize_series(df[col]),
            "by_trend_regime": summarize_group(df, "trend_regime", col),
            "by_volatility_regime": summarize_group(df, "volatility_regime", col),
            "by_drawdown_regime": summarize_group(df, "drawdown_regime", col),
            "by_leadership_asset": summarize_group(df, "leadership_asset", col),
            "by_asset": summarize_group(df, "asset", col),
        }

    return {
        "success": True,
        "row_count": int(len(df)),
        "return_columns": return_cols,
        "summaries": summaries,
    }


def summarize_series(series: pd.Series) -> dict[str, Any]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return {"count": 0}

    return {
        "count": int(s.count()),
        "win_rate": round(float((s > 0).mean()), 6),
        "mean": round(float(s.mean()), 8),
        "median": round(float(s.median()), 8),
        "min": round(float(s.min()), 8),
        "max": round(float(s.max()), 8),
    }


def summarize_group(df: pd.DataFrame, group_col: str, return_col: str) -> dict[str, Any]:
    if group_col not in df.columns:
        return {}

    result = {}
    for key, group in df.groupby(group_col, dropna=False):
        result[str(key)] = summarize_series(group[return_col])
    return result


def build_warnings(report: dict[str, Any]) -> list[str]:
    warnings = []

    if report["price_rows"] == 0:
        warnings.append("No usable price data found.")

    if report["outcome_rows"] == 0:
        warnings.append("No usable outcome/signal data found.")

    summary = report.get("return_summary", {})
    for col, data in (summary.get("summaries", {}) or {}).items():
        overall = data.get("overall", {})
        if overall.get("count", 0) < 30:
            warnings.append(f"Small sample size for {col}: {overall.get('count')} observations.")

    return warnings


def build_report(root: Path) -> dict[str, Any]:
    price_raw = read_csv(resolve(root, "output/price_data.csv"))
    price = normalize_price_data(price_raw)
    regimes = classify_regimes(price)

    outcomes_raw = load_outcomes(root)
    outcomes = normalize_outcomes(outcomes_raw)
    joined = join_regimes(outcomes, regimes)

    return_summary = summarize_returns(joined)

    report = {
        "success": True,
        "root": str(root),
        "price_rows": int(len(price)),
        "regime_rows": int(len(regimes)),
        "outcome_rows": int(len(outcomes)),
        "joined_rows": int(len(joined)),
        "outcome_source": outcomes_raw["_source_file"].iloc[0] if not outcomes_raw.empty and "_source_file" in outcomes_raw.columns else "",
        "return_summary": return_summary,
        "summary": "",
    }

    report["warnings"] = build_warnings(report)
    report["summary"] = (
        f"Investment Regime Validation joined {report['joined_rows']} outcome row(s) "
        f"against {report['regime_rows']} regime row(s). Warning count: {len(report['warnings'])}."
    )

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    MD_PATH.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Investment Regime Validation",
        "",
        report.get("summary", ""),
        "",
        "## Inputs",
        "",
        f"- Root: `{report.get('root')}`",
        f"- Price rows: `{report.get('price_rows')}`",
        f"- Regime rows: `{report.get('regime_rows')}`",
        f"- Outcome rows: `{report.get('outcome_rows')}`",
        f"- Joined rows: `{report.get('joined_rows')}`",
        f"- Outcome source: `{report.get('outcome_source')}`",
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

    lines.extend(["", "## Return Summaries", ""])

    summaries = ((report.get("return_summary", {}) or {}).get("summaries", {}) or {})
    for col, data in summaries.items():
        lines.extend([f"### {col}", ""])
        overall = data.get("overall", {})
        lines.extend([
            f"- Count: `{overall.get('count')}`",
            f"- Win rate: `{overall.get('win_rate')}`",
            f"- Mean: `{overall.get('mean')}`",
            f"- Median: `{overall.get('median')}`",
            "",
            "#### By Trend Regime",
            "",
        ])

        for regime, values in (data.get("by_trend_regime", {}) or {}).items():
            lines.append(
                f"- `{regime}`: count=`{values.get('count')}`, win=`{values.get('win_rate')}`, mean=`{values.get('mean')}`"
            )

        lines.extend(["", "#### By Volatility Regime", ""])

        for regime, values in (data.get("by_volatility_regime", {}) or {}).items():
            lines.append(
                f"- `{regime}`: count=`{values.get('count')}`, win=`{values.get('win_rate')}`, mean=`{values.get('mean')}`"
            )

        lines.append("")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(Path(args.root))
    print(report["success"])
    print(report["summary"])
    print(f"Warnings: {len(report.get('warnings', []))}")
    print(f"JSON: {JSON_PATH}")
    print(f"Markdown: {MD_PATH}")


if __name__ == "__main__":
    main()
