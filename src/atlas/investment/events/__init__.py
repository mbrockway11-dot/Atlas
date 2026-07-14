"""Atlas G.22 canonical event bus and event store."""

from .bus import EventBus, EventHandler
from .contracts import (
    SCHEMA_VERSION,
    AtlasEvent,
    EventCursor,
    EventDispatchResult,
    EventReplayResult,
    EventType,
)
from .errors import (
    DuplicateEventError,
    EventBusError,
    EventDispatchError,
    EventIntegrityError,
    EventValidationError,
)
from .persistence import (
    append_jsonl,
    atomic_write_json,
    canonical_json,
    compute_hash,
    read_jsonl,
    validate_hash_chain,
)
from .replay import ReplayHandler, replay_events
from .store import EventStore

__all__ = [
    "SCHEMA_VERSION",
    "AtlasEvent",
    "DuplicateEventError",
    "EventBus",
    "EventBusError",
    "EventCursor",
    "EventDispatchError",
    "EventDispatchResult",
    "EventHandler",
    "EventIntegrityError",
    "EventReplayResult",
    "EventStore",
    "EventType",
    "EventValidationError",
    "ReplayHandler",
    "append_jsonl",
    "atomic_write_json",
    "canonical_json",
    "compute_hash",
    "read_jsonl",
    "replay_events",
    "validate_hash_chain",
]
