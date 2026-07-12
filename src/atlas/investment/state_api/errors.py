"""Atlas State API exceptions."""

from __future__ import annotations


class AtlasStateAPIError(RuntimeError):
    """Base Atlas State API error."""


class CompiledStateNotFoundError(
    AtlasStateAPIError
):
    """Raised when the compiled state does not exist."""


class InvalidCompiledStateError(
    AtlasStateAPIError
):
    """Raised when the compiled state is malformed."""


class StateSectionNotFoundError(
    AtlasStateAPIError
):
    """Raised when a requested state section does not exist."""


class StateComponentNotFoundError(
    AtlasStateAPIError
):
    """Raised when a requested component does not exist."""
