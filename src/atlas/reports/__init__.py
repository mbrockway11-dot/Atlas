"""Atlas report generation public API."""

from atlas.reports.markdown import (
    build_profile_markdown_report,
    write_markdown_report,
)

__all__ = [
    "build_profile_markdown_report",
    "write_markdown_report",
]