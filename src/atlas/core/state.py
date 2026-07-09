
"""Atlas Core shared state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AtlasState:
    data: dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def has(self, key: str) -> bool:
        return key in self.data

    def to_dict(self) -> dict[str, Any]:
        return self.data
