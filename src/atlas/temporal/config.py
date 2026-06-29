"""Temporal Intelligence configuration."""

from __future__ import annotations


TEMPORAL_CONFIG_VERSION = "1.0"

DEFAULT_ZODIAC = "sidereal"
DEFAULT_AYANAMSA = "Lahiri"
DEFAULT_NODE_MODE = "Mean"
DEFAULT_HOUSE_SYSTEM = "Whole Sign"
DEFAULT_UNKNOWN_TIME = "12:00"

SUPPORTED_AYANAMSAS = [
    "Lahiri",
    "Raman",
    "Krishnamurti",
    "Fagan-Bradley",
]

SUPPORTED_NODE_MODES = [
    "Mean",
]

SUPPORTED_HOUSE_SYSTEMS = [
    "Whole Sign",
]