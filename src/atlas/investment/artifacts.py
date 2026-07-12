"""Canonical Atlas investment artifact registry.

This module centralizes shared artifact locations and safe read helpers without
owning subsystem business logic. Callers reference stable artifact keys rather
than repeating output paths and defensive CSV/JSON loading code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


ARTIFACTS: dict[str, Path] = {
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
    ),
    "meta_feature_interactions": Path(
        "output/investment_meta_research/feature_interactions.csv"
    ),
    "hypothesis_validation_results": Path(
        "output/investment_hypothesis_validation/"
        "hypothesis_validation_results.csv"
    ),
    "historical_alpha_validation_report": Path(
        "output/investment_historical_alpha_validation/"
        "historical_alpha_validation_report.json"
    ),
    "validated_variant_registry": Path(
        "output/investment_validated_variants/"
        "validated_variant_registry.csv"
    ),
    "variant_review_board": Path(
        "output/in