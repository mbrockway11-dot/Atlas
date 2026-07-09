
"""Atlas Core simple cache."""

from __future__ import annotations

from typing import Any


class AtlasCache:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def has(self, key: str) -> bool:
        return key in self.data
