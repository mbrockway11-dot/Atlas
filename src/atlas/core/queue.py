
"""Atlas Core execution queue."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class ExecutionQueueItem:
    node: str
    status: str = "PENDING"
    queue_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)


class ExecutionQueue:
    def __init__(self) -> None:
        self.items: list[ExecutionQueueItem] = []

    def add(self, node: str, metadata: dict[str, Any] | None = None) -> None:
        self.items.append(ExecutionQueueItem(node=node, metadata=metadata or {}))

    def to_dict(self) -> list[dict[str, Any]]:
        return [item.__dict__ for item in self.items]
