"""Report Atlas compiled-runtime health.

Surfaces the drift a working system will not complain about on its own:
artifacts compiled against an older feature schema, statistics built from a
corpus that has since moved, a stale or missing index.

Exits non-zero when anything is not OK, so it can gate a deploy or a cron
check.

    python scripts/compiled_runtime_health.py
    python scripts/compiled_runtime_health.py --deep
"""

from __future__ import annotations

import argparse
import json
import sys

from atlas.compiled.health import STATUS_OK, build_runtime_health


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Report Atlas compiled-runtime health."
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help=(
            "Validate every artifact against its source ACF. Accurate but "
            "walks the whole corpus; the default check reads only headers."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only the overall status and any problems.",
    )
    return parser


def main() -> int:
    """Print the health report."""
    args = build_parser().parse_args()

    health = build_runtime_health(deep=args.deep)

    if args.quiet:
        report = {
            "status": health.status,
            "healthy": health.healthy,
            "problems": [c.to_dict() for c in health.problems()],
        }
    else:
        report = health.to_dict()

    print(json.dumps(report, indent=2, default=str))

    return 0 if health.status == STATUS_OK else 1


if __name__ == "__main__":
    sys.exit(main())
