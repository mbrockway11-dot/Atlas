"""Project-root-aware paths for historical validation artifacts."""

from pathlib import Path

from atlas.services.profile_path_service import PROJECT_ROOT


RESEARCH_DIR = PROJECT_ROOT / "research" / "historical_validation"
OUTPUT_DIR = PROJECT_ROOT / "output" / "historical_validation"
PILOT_REGISTRY_PATH = RESEARCH_DIR / "apollo11_pilot_registry.json"
CHECKPOINT_PATH = OUTPUT_DIR / "run_checkpoint.json"


def output_path(name: str) -> Path:
    return OUTPUT_DIR / name
