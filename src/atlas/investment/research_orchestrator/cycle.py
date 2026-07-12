"""Continuous Research Orchestrator cycle controller."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.research_orchestrator.executor import execute_job
from atlas