
"""Atlas Core script-backed node wrapper."""

from __future__ import annotations

import subprocess
import sys
from typing import Any

from atlas.core.context import AtlasContext
from atlas.core.node import Node, NodeResult
from atlas.core.state import AtlasState


class ScriptNode(Node):
    """Wrap an existing script as an Atlas Core node."""

    def __init__(
        self,
        *,
        name: str,
        command: list[str],
        requires: list[str] | None = None,
        provides: list[str] | None = None,
        output_key: str | None = None,
    ) -> None:
        self.name = name
        self.command = command
        self.requires = requires or []
        self.provides = provides or []
        self.output_key = output_key or (self.provides[0] if self.provides else name)

    def execute(self, state: AtlasState, context: AtlasContext) -> NodeResult:
        proc = subprocess.run(
            [sys.executable, *self.command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        output = {
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "command": " ".join([sys.executable, *self.command]),
        }

        return NodeResult(
            name=self.name,
            success=proc.returncode == 0,
            output_key=self.output_key,
            output=output,
            error=None if proc.returncode == 0 else proc.stderr.strip(),
        )
