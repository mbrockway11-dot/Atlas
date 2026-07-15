"""Canonical LYFE-to-execution orchestration entrypoint.

Connects existing Atlas components without introducing new trading logic:
LYFE instruction -> portfolio intent -> OrderIntent -> risk -> paper/broker route.

Safety guarantees:
- human approval is required when the LYFE instruction requires it;
- live broker capabilities are rejected;
- paper execution remains the default route;
- short instructions remain deferred by the existing LYFE portfolio mapper;
- every result is returned as one deterministic bridge report.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing