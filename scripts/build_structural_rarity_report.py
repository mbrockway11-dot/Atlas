
"""Build Atlas Structural Rarity report."""

from __future__ import annotations

import json
from pathlib import Path

from atlas.population.structural_rarity import build_structural_rarity_report


OUT = Path("output/population/structural_rarity_report.json")


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    report = build_structural_rarity_report()

    with OUT.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print(f"wrote {OUT}")
    print("success:", report.get("success"))
    print("profiles:", report.get("profile_count"))
    print("top outliers:")
    for item in report.get("top_outliers", [])[:20]:
        print(
            "-",
            item.get("profile_key"),
            item.get("overall_rarity_score"),
            item.get("outlier_label"),
            "; ".join(item.get("outlier_reasons", [])[:3]),
        )


if __name__ == "__main__":
    main()
