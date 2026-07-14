"""Event bus errors for Atlas G.22."""


class EventBusError(RuntimeError):
    """Base event bus error."""


class EventValidationError(EventBusError):
    """Event failed schema or safety validation."""


class DuplicateEventError(EventBusError):
    """Event ID has already been stored."""


class EventIntegrityError(EventBusError):
    """Event store integrity or hash-chain validation failed."""


class EventDispatchError(EventBusError):
    """One or more event handlers failed."""


__all__ = [
    "DuplicateEventError",
    "EventBusError",
    "EventDispatchError",
    "EventIntegrityError",
    "EventValidationError",
]
