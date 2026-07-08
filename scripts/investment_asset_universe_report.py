
"""Investment Asset Universe Report.

Inspects current investment engine asset coverage and recommends a wider universe.

Outputs:
- output/investment_universe/investment_asset_universe_report.json
- output/investment_universe/investment_asset_universe_report.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_ROOT = Path(r"C:\Users\lyfe1\OneDrive\Desktop\sigil-engine")
OUT_DIR = Path("output/investment_universe")
JSON_PATH = OUT_DIR / "investment_asset_universe_report.json"
MD_PATH = OUT_DIR / "investment_asset_universe_report.md"

TARGET_ASSETS = [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "BNB-USD",
    "XRP-USD",
    "ADA-USD",
    "DOGE-USD",
    "LINK-USD",
    "AVAX-USD",
    "TRX-USD",
    "SUI-USD",
]


def read_price_data(root: Path) -> pd.DataFrame:
    path = root / "output" / "price_data.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def detect_asset_col(df: pd.DataFrame) -> str:
    for col in ["asset", "symbol", "ticker"]:
        if col in df.columns:
            return col
    for col in df.columns:
        if "asset" in col.lower() or "symbol" in col.lower() or "ticker" in col.lower():
            return col
    return ""


def detect_date_col(df: pd.DataFrame) -> str:
    for col in ["date", "timestamp", "datetime", "time"]:
        if col in df.columns:
            return col
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            return col
    return ""


def build_asset_universe_report(root: Path, target_assets: list[str] | None = None) -> dict[str, Any]:
    target_assets = target_assets or TARGET_ASSETS
    df = read_price_data(root)

    if df.empty:
        report = {
            "success": False,
            "root": str(root),
            "error": "No price_data.csv found or file is empty.",
            "target_assets": target_assets,
            "current_assets": [],
            "missing_assets": target_assets,
            "summary": "No usable price data found.",
        }
        write_outputs(report)
        return report

    asset_col = detect_asset_col(df)
    date_col = detect_date_col(df)

    if not asset_col:
        report = {
            "success": False,
            "root": str(root),
            "error": "Could not detect asset column.",
            "columns": list(df.columns),
            "target_assets": target_assets,
            "summary": "Asset universe report failed because no asset column was detected.",
        }
        write_outputs(report)
        return report

    current_assets = sorted(str(x) for x in df[asset_col].dropna().unique().tolist())
    missing_assets = [asset for asset in target_assets if asset not in current_assets]
    extra_assets = [asset for asset in current_assets if asset not in target_assets]

    rows_by_asset = {
        str(k): int(v)
        for k, v in df[asset_col].value_counts(dropna=False).to_dict().items()
    }

    coverage = {}

    if date_col:
        df["_dt"] = pd.to_datetime(df[date_col], errors="coerce")
        for asset, group in df.groupby(asset_col):
            dates = group["_dt"].dropna()
            coverage[str(asset)] = {
                "rows": int(len(group)),
                "date_min": str(dates.min()) if not dates.empty else None,
                "date_max": str(dates.max()) if not dates.empty else None,
                "invalid_dates": int(group["_dt"].isna().sum()),
            }
    else:
        for asset, group in df.groupby(asset_col):
            coverage[str(asset)] = {
                "rows": int(len(group)),
            }

    report = {
        "success": True,
        "root": str(root),
        "price_data_path": str(root / "output" / "price_data.csv"),
        "row_count": int(len(df)),
        "asset_column": asset_col,
        "date_column": date_col,
        "target_assets": target_assets,
        "target_count": len(target_assets),
        "current_assets": current_assets,
        "current_count": len(current_assets),
        "missing_assets": missing_assets,
        "missing_count": len(missing_assets),
        "extra_assets": extra_assets,
        "extra_count": len(extra_assets),
        "rows_by_asset": rows_by_asset,
        "coverage": coverage,
        "recommended_next_universe": target_assets,
        "summary": (
            f"Investment universe report found {len(current_assets)} current asset(s) "
            f"against {len(target_assets)} target asset(s). "
            f"Missing: {len(missing_assets)}."
        ),
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    MD_PATH.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Investment Asset Universe Report",
        "",
        report.get("summary", ""),
        "",
        "## Current Coverage",
        "",
        f"- Root: `{report.get('root')}`",
        f"- Price data path: `{report.get('price_data_path', 'n/a')}`",
        f"- Rows: `{report.get('row_count', 0)}`",
        f"- Current assets: `{report.get('current_count', 0)}`",
        f"- Target assets: `{report.get('target_count', 0)}`",
        f"- Missing assets: `{report.get('missing_count', 0)}`",
        "",
        "## Current Assets",
        "",
    ]

    for asset in report.get("current_assets", []) or []:
        coverage = (report.get("coverage", {}) or {}).get(asset, {})
        lines.append(
            f"- `{asset}` rows=`{coverage.get('rows')}` "
            f"from `{coverage.get('date_min')}` to `{coverage.get('date_max')}`"
        )

    lines.extend(["", "## Missing Target Assets", ""])

    missing = report.get("missing_assets", []) or []
    if missing:
        for asset in missing:
            lines.append(f"- `{asset}`")
    else:
        lines.append("- None.")

    lines.extend(["", "## Recommended Target Universe", ""])

    for asset in report.get("recommended_next_universe", []) or []:
        lines.append(f"- `{asset}`")

    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_asset_universe_report(Path(args.root))
    print(report["success"])
    print(report["summary"])
    print("Current:", report.get("current_assets", []))
    print("Missing:", report.get("missing_assets", []))
    print(f"JSON: {JSON_PATH}")
    print(f"Markdown: {MD_PATH}")


if __name__ == "__main__":
    main()
