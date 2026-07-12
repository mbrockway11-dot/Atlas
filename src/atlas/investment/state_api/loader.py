"""Atlas compiled-state loading and caching."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from atlas.investment.state_api.config import (
    COMPILED_STATE_PATH,
)
from atlas.investment.state_api.errors import (
    CompiledStateNotFoundError,
    InvalidCompiledStateError,
)


_STATE_CACHE: dict[str, Any] = {
    "path": None,
    "mtime_ns": None,
    "state": None,
}


def load_compiled_state(
    path: Path | str | None = None,
    *,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Load and validate a compiled Atlas state."""
    resolved = Path(
        path
        if path is not None
        else COMPILED_STATE_PATH
    )

    if (
        not resolved.exists()
        or not resolved.is_file()
    ):
        raise CompiledStateNotFoundError(
            "Compiled Atlas state was not found: "
            f"{resolved}"
        )

    mtime_ns = resolved.stat().st_mtime_ns

    if (
        use_cache
        and _STATE_CACHE["path"]
        == str(resolved.resolve())
        and _STATE_CACHE["mtime_ns"]
        == mtime_ns
        and isinstance(
            _STATE_CACHE["state"],
            dict,
        )
    ):
        return copy.deepcopy(
            _STATE_CACHE["state"]
        )

    try:
        state = json.loads(
            resolved.read_text(
                encoding="utf-8"
            )
        )
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        OSError,
    ) as error:
        raise InvalidCompiledStateError(
            "Unable to read compiled Atlas state: "
            f"{error}"
        ) from error

    validate_loaded_state(
        state
    )

    _STATE_CACHE["path"] = str(
        resolved.resolve()
    )
    _STATE_CACHE["mtime_ns"] = (
        mtime_ns
    )
    _STATE_CACHE["state"] = (
        copy.deepcopy(state)
    )

    return copy.deepcopy(state)


def validate_loaded_state(
    state: Any,
) -> None:
    """Validate the minimum compiled-state contract."""
    if not isinstance(state, dict):
        raise InvalidCompiledStateError(
            "Compiled state root must be an object."
        )

    required_keys = {
        "version",
        "schema_version",
        "state_hash",
        "sections",
        "validation",
        "contract",
    }

    missing = sorted(
        required_keys
        - set(state)
    )

    if missing:
        raise InvalidCompiledStateError(
            "Compiled state is missing required keys: "
            + ", ".join(missing)
        )

    if not isinstance(
        state.get("sections"),
        dict,
    ):
        raise InvalidCompiledStateError(
            "Compiled state sections must be an object."
        )

    state_hash = state.get(
        "state_hash"
    )

    if (
        not isinstance(
            state_hash,
            str,
        )
        or len(state_hash) != 64
    ):
        raise InvalidCompiledStateError(
            "Compiled state hash must be a "
            "64-character SHA-256 value."
        )


def clear_state_cache() -> None:
    """Clear the in-process compiled-state cache."""
    _STATE_CACHE["path"] = None
    _STATE_CACHE["mtime_ns"] = None
    _STATE_CACHE["state"] = None
