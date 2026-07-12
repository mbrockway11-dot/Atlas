"""Incremental dependency freshness for the canonical research DAG.

This module does not define another graph. It evaluates the dependency edges
already owned by the canonical job registry and reports whether an upstream
output is newer than the current job output.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from atlas.investment