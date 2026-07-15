"""Canonical LYFE-to-execution orchestration entrypoint.

Connects existing Atlas components without introducing new trading logic:
LYFE instruction -> portfolio intent -> OrderIntent -> risk -> broker/paper execution.

All routes remain paper-only. Human approval is mandatory for executable LYFE
instructions, and live execution is never authorized by this module.
"""

from __future__ import annotations

from dataclasses import asdict