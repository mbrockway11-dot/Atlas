
"""Kill switch state."""

from __future__ import annotations

from pathlib import Path


KILL_SWITCH_PATH = Path("output/investment_safety/KILL_SWITCH_ON")


def kill_switch_active() -> bool:
    return KILL_SWITCH_PATH.exists()


def enable_kill_switch(reason: str = "") -> None:
    KILL_SWITCH_PATH.parent.mkdir(parents=True, exist_ok=True)
    KILL_SWITCH_PATH.write_text(reason or "Manual kill switch enabled.", encoding="utf-8")


def disable_kill_switch() -> None:
    if KILL_SWITCH_PATH.exists():
        KILL_SWITCH_PATH.unlink()
