"""Plugin manifest support for Atlas."""

from __future__ import annotations

from pathlib import Path


def load_enabled_plugins(path: str | Path) -> set[str] | None:
    """Load enabled plugin names from a simple manifest.

    Supported format:

    plugins:
      identity: true
      intelligence: true
      experimental: false

    This avoids requiring PyYAML.
    """
    manifest_path = Path(path)

    if not manifest_path.exists():
        return None

    enabled: set[str] = set()
    in_plugins = False

    for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line == "plugins:":
            in_plugins = True
            continue

        if not in_plugins or ":" not in line:
            continue

        name, value = line.split(":", 1)
        name = name.strip()
        value = value.strip().lower()

        if value in {"true", "yes", "1", "enabled"}:
            enabled.add(name)

    return enabled