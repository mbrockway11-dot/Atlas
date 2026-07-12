"""Canonical Atlas investment artifact registry.

This module is the single source of truth for stable investment artifact paths.
Subsystem business logic remains local; consumers resolve named artifacts here
and use the shared safe readers instead of repeating paths and parsing logic.
"""

from __future__ import annotations

import json
