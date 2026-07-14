"""In-process deterministic event bus for Atlas G.22."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from .contracts import AtlasEvent, EventDispatchResult, EventType
from .errors import EventDispatchError
from .store import EventStore


EventHandler = Callable[[AtlasEvent], Any]


class EventBus:
    def __init__(self, *, store: EventStore) -> None:
        self.store = store
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(
        self,
        event_type: EventType | str,
        handler: EventHandler,
    ) -> None:
        key = event_type.value if isinstance(event_type, EventType) else str(event_type)
        key = key.upper()
        if handler not in self._handlers[key]:
            self._handlers[key].append(handler)

    def unsubscribe(
        self,
        event_type: EventType | str,
        handler: EventHandler,
    ) -> None:
        key = event_type.value if isinstance(event_type, EventType) else str(event_type)
        key = key.upper()
        if handler in self._handlers.get(key, []):
            self._handlers[key].remove(handler)

    def publish(
        self,
        event: AtlasEvent,
        *,
        raise_on_handler_error: bool = False,
    ) -> EventDispatchResult:
        stored = self.store.append(event)
        handlers = list(self._handlers.get(stored.event_type.value, []))
        errors: list[str] = []
        succeeded = 0

        for handler in handlers:
            try:
                handler(stored)
                succeeded += 1
            except Exception as exc:
                errors.append(f"{handler.__name__}: {exc}")

        result = EventDispatchResult(
            event_id=stored.event_id,
            handlers_matched=len(handlers),
            handlers_succeeded=succeeded,
            handlers_failed=len(errors),
            errors=tuple(errors),
        )

        if errors and raise_on_handler_error:
            raise EventDispatchError("; ".join(errors))
        return result


__all__ = ["EventBus", "EventHandler"]
