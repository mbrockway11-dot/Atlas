"""Project paths for symbolic-behavior validation artifacts."""

from pathlib import Path

from atlas.services.profile_path_service import PROJECT_ROOT


RESEARCH_DIR = PROJECT_ROOT / "research" / "symbolic_behavior"
OUTPUT_DIR = PROJECT_ROOT / "output" / "symbolic_behavior"
PILOT_REGISTRY_PATH = RESEARCH_DIR / "behavior_observation_pilot.v1.json"
CHECKPOINT_PATH = OUTPUT_DIR / "run_checkpoint.json"


def output_path(name: str) -> Path:
    return OUTPUT_DIR / name
