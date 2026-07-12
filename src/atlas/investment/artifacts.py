"""Canonical Atlas investment artifact registry.

This module owns shared artifact locations and safe key-based reads. Business
logic remains inside each subsystem; callers use stable keys instead of
repeating paths or defensive CSV/JSON parsing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


ARTIFACTS: dict[str, Path] = {
    # Meta research and validation.
    "meta_hypotheses": Path(
        "output/investment_meta_research/hypothesis_library.csv"
    ),
    "meta_research_priorities": Path(
        "output/investment_meta_research/research_priorities.csv"
    ),
    "meta_failure_modes": Path(
        "output/investment_meta_research/engine_failure_modes.csv"
    ),
    "meta_family_gaps": Path(
        "output/investment_meta_research/engine_family_gaps.csv"