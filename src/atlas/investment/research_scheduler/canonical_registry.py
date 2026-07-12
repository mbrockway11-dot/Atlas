"""Canonical composed Atlas research job registry.

The legacy registry remains unchanged for compatibility.  This module adds
newer research-program and evidence stages, adjusts the validated-variant
handoff to consume accumulated evidence, and exposes one composed registry
to the scheduler and orchestrator.
"""

from __future__ import annotations

