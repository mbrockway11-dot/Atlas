
"""Build Atlas Structural Impact report."""

from __future__ import annotations

import json
from pathlib import Path

from atlas.population.structural_impact import build_structural_impact_report


OUT = Path("output/population/structural_impact_report.json")


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    report = build_structural_impact_report()

    with OUT.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print(f"wrote {OUT}")
    print("success:", report.get("success"))
    print("profiles:", report.get("profile_count"))
    print("top impact profiles:")
    for item in report.get("top_impact_profiles", [])[:25]:
        print(
            "-",
            item.get("profile_key"),
            item.get("impact_percent"),
            item.get("impact_label"),
            "; ".join(item.get("impact_reasons", [])[:3]),
        )


if __name__ == "__main__":
    main()
