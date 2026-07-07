
"""Investment system audit.

Inspects existing trading-system outputs and writes:
- output/investment_audit/investment_system_audit.json
- output/investment_audit/investment_system_audit.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT_DIR = Path(".")
OUTPUT_DIR = Path("output")
AUDIT_DIR = OUTPUT_DIR / "investment_audit"
JSON_PATH = AUDIT_DIR / "investment_system_audit.json"
MD_PATH = AUDIT_DIR / "investment_system_audit.md"


CANDIDATE_FILES = {
    "price_data": [
        "output/price_data.csv",
        "output/btc_price_data.csv",
        "output/eth_price_data.csv",
        "output/sol_price_data.csv",
    ],
    "leader_laggard": [
        "output/leader_laggard_summary.csv",
    ],
    "forward_outcomes": [
        "output/forward_outcomes.csv",
    ],
    "pre_signal": [
        "output/pre_signal_raw.csv",
        "output/pre_signal_candidates.csv",
        "output/pre_signal_candidates_v5.csv",
        "output/pre_signal_candidates_excess.csv",
    ],
    "live_signals": [
        "output/live_signal_v5.csv",
        "output/backfilled_live_signals_v5.csv",
        "output/v32_ab_live_signal_snapshot.csv",
        "output/v32_ab_live_execution.csv",
    ],
    "equity": [
        "output/equity_curve_v5.csv",
        "output/equity_compare_summary_v5.csv",
        "output/equity_compare_trades_v5.csv",
    ],
}


def resolve_path(path: str | Path) -> Path:
    target = Path(path)
    if target.is_absolute():
        return target
    return ROOT_DIR / target


def read_csv_safe(path: str | Path) -> tuple[pd.DataFrame | None, str]:
    target = resolve_path(path)

    if not target.exists():
        return None, "missing"

    try:
        return pd.read_csv(target), "ok"
    except Exception as exc:
        return None, f"error: {exc}"


def audit_file(path: str | Path) -> dict[str, Any]:
    df, status = read_csv_safe(path)
    result: dict[str, Any] = {
        "path": str(path),
        "status": status,
        "exists": resolve_path(path).exists(),
        "resolved_path": str(resolve_path(path)),
    }

    if df is None:
        return result

    result.update(
        {
            "rows": int(len(df)),
            "columns": list(df.columns),
            "column_count": int(len(df.columns)),
            "missing_values": {
                col: int(df[col].isna().sum())
                for col in df.columns
                if int(df[col].isna().sum()) > 0
            },
            "duplicate_rows": int(df.duplicated().sum()),
        }
    )

    date_col = detect_date_col(df)
    asset_col = detect_asset_col(df)

    if date_col:
        dates = pd.to_datetime(df[date_col], errors="coerce")
        valid_dates = dates.dropna()
        result["date_column"] = date_col
        result["date_min"] = str(valid_dates.min()) if not valid_dates.empty else None
        result["date_max"] = str(valid_dates.max()) if not valid_dates.empty else None
        result["invalid_dates"] = int(dates.isna().sum())

        if asset_col:
            result["duplicate_asset_timestamps"] = int(
                df.duplicated(subset=[asset_col, date_col]).sum()
            )
        else:
            result["duplicate_timestamps"] = int(df.duplicated(subset=[date_col]).sum())

    if asset_col:
        result["asset_column"] = asset_col
        result["asset_count"] = int(df[asset_col].nunique(dropna=True))
        result["assets"] = sorted([str(x) for x in df[asset_col].dropna().unique().tolist()])[:100]
        result["rows_by_asset"] = {
            str(k): int(v)
            for k, v in df[asset_col].value_counts(dropna=False).to_dict().items()
        }

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        result["numeric_summary"] = {
            col: {
                "mean": safe_float(df[col].mean()),
                "median": safe_float(df[col].median()),
                "min": safe_float(df[col].min()),
                "max": safe_float(df[col].max()),
            }
            for col in numeric_cols[:25]
        }

    return result


def detect_date_col(df: pd.DataFrame) -> str:
    candidates = [
        "date",
        "timestamp",
        "datetime",
        "time",
        "entry_time",
        "session_date",
    ]
    lowered = {col.lower(): col for col in df.columns}

    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]

    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            return col

    return ""


def detect_asset_col(df: pd.DataFrame) -> str:
    candidates = [
        "asset",
        "symbol",
        "leader_asset",
        "laggard_asset",
        "trade_asset",
    ]
    lowered = {col.lower(): col for col in df.columns}

    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]

    for col in df.columns:
        if "asset" in col.lower() or "symbol" in col.lower():
            return col

    return ""


def safe_float(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return round(float(value), 8)
    except Exception:
        return None


def audit_signals() -> dict[str, Any]:
    paths = CANDIDATE_FILES["live_signals"] + CANDIDATE_FILES["pre_signal"]
    rows = []

    for path in paths:
        df, status = read_csv_safe(path)
        if df is None:
            continue

        row: dict[str, Any] = {
            "path": path,
            "rows": int(len(df)),
        }

        asset_col = detect_asset_col(df)
        if asset_col:
            row["asset_count"] = int(df[asset_col].nunique(dropna=True))
            row["rows_by_asset"] = {
                str(k): int(v)
                for k, v in df[asset_col].value_counts(dropna=False).to_dict().items()
            }

        for col in df.columns:
            lower = col.lower()
            if lower in {"action", "signal_state", "decision", "side", "direction", "strategy", "strategy_type"}:
                row[f"{col}_counts"] = {
                    str(k): int(v)
                    for k, v in df[col].value_counts(dropna=False).to_dict().items()
                }

        rows.append(row)

    return {
        "success": True,
        "signal_files_found": len(rows),
        "files": rows,
    }


def audit_forward_returns() -> dict[str, Any]:
    candidates = [
        "output/backfilled_live_signals_v5.csv",
        "output/forward_outcomes.csv",
    ]

    reports = []

    for path in candidates:
        df, status = read_csv_safe(path)
        if df is None:
            continue

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        return_cols = [
            col for col in numeric_cols
            if any(token in col.lower() for token in ["return", "ret", "outcome", "forward"])
        ]

        report = {
            "path": path,
            "rows": int(len(df)),
            "return_columns": return_cols,
            "summary": {},
        }

        asset_col = detect_asset_col(df)

        for col in return_cols[:20]:
            series = pd.to_numeric(df[col], errors="coerce").dropna()
            if series.empty:
                continue

            report["summary"][col] = {
                "count": int(series.count()),
                "win_rate_gt_0": safe_float((series > 0).mean()),
                "mean": safe_float(series.mean()),
                "median": safe_float(series.median()),
                "min": safe_float(series.min()),
                "max": safe_float(series.max()),
            }

            if asset_col:
                by_asset = {}
                for asset, group in df.groupby(asset_col):
                    g = pd.to_numeric(group[col], errors="coerce").dropna()
                    if not g.empty:
                        by_asset[str(asset)] = {
                            "count": int(g.count()),
                            "win_rate_gt_0": safe_float((g > 0).mean()),
                            "mean": safe_float(g.mean()),
                            "median": safe_float(g.median()),
                        }
                report["summary"][col]["by_asset"] = by_asset

        reports.append(report)

    return {
        "success": True,
        "reports": reports,
    }


def build_warnings(audit: dict[str, Any]) -> list[str]:
    warnings = []

    price_files = audit["files"].get("price_data", [])
    found_price = [item for item in price_files if item.get("status") == "ok"]

    if not found_price:
        warnings.append("No price data files found.")

    signal_report = audit.get("signals", {})
    if signal_report.get("signal_files_found", 0) == 0:
        warnings.append("No signal files found.")

    for group, files in audit["files"].items():
        for item in files:
            if item.get("status") == "ok" and item.get("rows", 0) < 30:
                warnings.append(f"Small sample size in {item.get('path')}: {item.get('rows')} rows.")

            if item.get("missing_values"):
                warnings.append(f"Missing values detected in {item.get('path')}.")

            if item.get("duplicate_rows", 0) > 0:
                warnings.append(f"Duplicate rows detected in {item.get('path')}.")

            if item.get("duplicate_asset_timestamps", 0) > 0:
                warnings.append(f"Duplicate asset timestamps detected in {item.get('path')}.")

    return warnings


def build_investment_system_audit() -> dict[str, Any]:
    files = {}

    for group, paths in CANDIDATE_FILES.items():
        files[group] = [audit_file(path) for path in paths]

    audit = {
        "success": True,
        "audit": "investment_system_audit",
        "files": files,
        "signals": audit_signals(),
        "forward_returns": audit_forward_returns(),
    }

    audit["warnings"] = build_warnings(audit)
    audit["summary"] = build_summary(audit)

    write_outputs(audit)
    return audit


def build_summary(audit: dict[str, Any]) -> str:
    found = 0
    total = 0
    rows = 0

    for group_files in audit.get("files", {}).values():
        for item in group_files:
            total += 1
            if item.get("status") == "ok":
                found += 1
                rows += int(item.get("rows", 0))

    warnings = len(audit.get("warnings", []))

    return (
        f"Investment system audit inspected {total} expected file(s), found {found}, "
        f"and scanned {rows} total row(s). Warning count: {warnings}."
    )


def write_outputs(audit: dict[str, Any]) -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    JSON_PATH.write_text(
        json.dumps(audit, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    MD_PATH.write_text(
        build_markdown(audit),
        encoding="utf-8",
    )


def build_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Investment System Audit",
        "",
        audit.get("summary", ""),
        "",
        "## Warnings",
        "",
    ]

    warnings = audit.get("warnings", [])
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- No warnings.")

    lines.extend(["", "## File Inventory", ""])

    for group, files in audit.get("files", {}).items():
        lines.extend([f"### {group}", ""])
        for item in files:
            lines.append(
                f"- `{item.get('path')}` ? `{item.get('status')}`"
                f" rows=`{item.get('rows', 'n/a')}`"
            )
        lines.append("")

    lines.extend(["## Signals", ""])

    signals = audit.get("signals", {}) or {}
    lines.append(f"- Signal files found: `{signals.get('signal_files_found', 0)}`")
    for item in signals.get("files", []):
        lines.append(f"- `{item.get('path')}` rows=`{item.get('rows')}`")

    lines.extend(["", "## Forward Returns", ""])

    for report in (audit.get("forward_returns", {}) or {}).get("reports", []):
        lines.extend([f"### {report.get('path')}", ""])
        for col, values in report.get("summary", {}).items():
            lines.extend([
                f"#### {col}",
                f"- Count: `{values.get('count')}`",
                f"- Win rate > 0: `{values.get('win_rate_gt_0')}`",
                f"- Mean: `{values.get('mean')}`",
                f"- Median: `{values.get('median')}`",
                f"- Min: `{values.get('min')}`",
                f"- Max: `{values.get('max')}`",
                "",
            ])

    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Root folder of investment/sigil-engine project")
    return parser.parse_args()


def main() -> None:
    global ROOT_DIR
    args = parse_args()
    ROOT_DIR = Path(args.root)
    audit = build_investment_system_audit()
    print(audit["success"])
    print(audit["summary"])
    print(f"Warnings: {len(audit.get('warnings', []))}")
    print(f"JSON: {JSON_PATH}")
    print(f"Markdown: {MD_PATH}")


if __name__ == "__main__":
    main()
