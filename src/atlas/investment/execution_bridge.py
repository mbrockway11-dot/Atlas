"""Canonical LYFE-to-execution orchestration entrypoint.

Connects existing Atlas components without introducing new trading logic:
LYFE instruction -> portfolio intent -> OrderIntent -> risk -> broker/paper execution.
Live execution remains disabled by the underlying broker and execution gates.
"""

from __future__ import annotations

from dataclasses import fields
from typing import Any, Mapping

from atlas.investment.brok