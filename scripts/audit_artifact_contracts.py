"""Audit Atlas generated artifact contracts.

Checks which generated artifacts exist, which code files reference them,
and which profile folders are incomplete.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_DIRS = [
    ROOT / "src",
    ROOT / "dashboard",
    ROOT / "scripts",
]

PROFILE_DIR = ROOT / "output" / "library" / "profiles"
REPORT_PATH = ROOT / "output" / "artifact_contract_audit.csv"

ARTIFACTS = [
    "profile_summary.json",
    "profile_interpretation.json",
        "profile.acf.json",
    "profile.intake.json",
    "codex_report.md",
]


def find_references(artifact: str) -> list[str]:
    """Return source files referencing an artifact filename."""
    matches: list[str] = []

    for base in SRC_DIRS:
        if not base.exists():
            continue

        for path in base.rglob("*.py"):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            if artifact in text:
                matches.append(str(path.relative_to(ROOT)))

    return sorted(matches)


def audit_profiles() -> list[dict[str, str]]:
    """Audit generated profile folders."""
    rows: list[dict[str, str]] = []

    if not PROFILE_DIR.exists():
        return rows

    for profile in sorted(p for p in PROFILE_DIR.iterdir() if p.is_dir()):
        row: dict[str, str] = {"profile": profile.name}

        for artifact in ARTIFACTS:
            row[artifact] = "yes" if (profile / artifact).exists() else "no"

        missing = [
            artifact
            for artifact in ARTIFACTS
            if row[artifact] == "no"
        ]

        row["missing_count"] = str(len(missing))
        row["missing"] = ", ".join(missing)

        rows.append(row)

    return rows


def print_contract_matrix() -> None:
    """Print artifact reference contract matrix."""
    print("# Atlas Artifact Contract Audit")
    print()
    print("## Artifact References")
    print()

    for artifact in ARTIFACTS:
        refs = find_references(artifact)

        print(f"### {artifact}")
        print(f"- references: {len(refs)}")

        if refs:
            for ref in refs:
                print(f"  - {ref}")
        else:
            print("  - none")

        print()


def write_profile_report(rows: list[dict[str, str]]) -> None:
    """Write profile artifact audit CSV."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "profile",
        *ARTIFACTS,
        "missing_count",
        "missing",
    ]

    with REPORT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_profile_summary(rows: list[dict[str, str]]) -> None:
    """Print summary of missing artifacts."""
    print("## Profile Artifact Summary")
    print()

    print(f"- profiles: {len(rows)}")

    incomplete = [
        row for row in rows
        if int(row["missing_count"]) > 0
    ]

    print(f"- incomplete_profiles: {len(incomplete)}")
    print(f"- report: {REPORT_PATH.relative_to(ROOT)}")
    print()

    print("## Most Common Missing Artifacts")
    print()

    counts = {
        artifact: sum(1 for row in rows if row[artifact] == "no")
        for artifact in ARTIFACTS
    }

    for artifact, count in sorted(counts.items(), key=lambda item: item[1], reverse=True):
        print(f"- {artifact}: {count}")

    print()

    print("## First 25 Incomplete Profiles")
    print()

    for row in incomplete[:25]:
        print(f"- {row['profile']}: {row['missing']}")


def main() -> None:
    """Run audit."""
    print_contract_matrix()

    rows = audit_profiles()
    write_profile_report(rows)
    print_profile_summary(rows)


if __name__ == "__main__":
    main()
