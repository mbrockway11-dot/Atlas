from pathlib import Path

pages = sorted(Path("dashboard/pages").glob("*.py"))

atlas_profile_patterns = [
    "build_atlas_profile",
    "AtlasProfile",
    "atlas_profile_service",
    "intelligence_service",
    "get_intelligence_payload",
    "atlas.services",
]

direct_backend_patterns = [
    "from atlas.research",
    "from atlas.temporal",
    "from atlas.calibration",
    "from atlas.graph",
    "from atlas.intelligence.engine",
]

print("\nDASHBOARD ATLASPROFILE AUDIT")
print("=" * 80)

for page in pages:
    text = page.read_text(encoding="utf-8", errors="ignore")

    uses_atlas_profile = any(pattern in text for pattern in atlas_profile_patterns)
    direct_backend = [
        pattern for pattern in direct_backend_patterns
        if pattern in text
    ]

    status = "USES AtlasProfile" if uses_atlas_profile else "NOT migrated"
    backend = ", ".join(direct_backend) if direct_backend else "no direct backend imports detected"

    print(f"{page}: {status} | {backend}")
