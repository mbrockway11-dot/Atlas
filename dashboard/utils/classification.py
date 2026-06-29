"""Dashboard classification helpers."""

import json

from atlas.acf.builder import build_acf_profile
from atlas.library.profile_library import LIBRARY_DIR


def load_or_build_acf_classification(profile_key: str, name: str) -> dict:
    """Load classification from ACF if available, otherwise build it."""
    acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

    if acf_path.exists():
        data = json.loads(acf_path.read_text(encoding="utf-8"))
        classification = data.get("essence", {}).get("classification")

        if classification and "meanings" in classification:
            return classification

    acf = build_acf_profile(name=name)
    classification = acf["essence"]["classification"]

    acf_path.parent.mkdir(parents=True, exist_ok=True)
    acf_path.write_text(
        json.dumps(acf, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return classification