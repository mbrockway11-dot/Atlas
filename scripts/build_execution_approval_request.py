"""Build a supervised paper execution approval request."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from atlas.investment.approval import ApprovalError, ApprovalService, OrderPreview


def read_object(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/investment_approval"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        payload = read_object(args.input)
        service = ApprovalService(output_dir=args.output_dir)
        request = service.create_request(
            decision_id=str(payload["decision_id"]),
            orchestration_run_id=str(payload["orchestration_run_id"]),
            portfolio_id=str(payload["portfolio_id"]),
            risk_report_id=str(payload["risk_report_id"]),
            intent_ids=tuple(payload["intent_ids"]),
            order_previews=tuple(
                OrderPreview(**item) for item in payload["order_previews"]
            ),
            expires_in_minutes=int(payload.get("expires_in_minutes", 30)),
            metadata=dict(payload.get("metadata", {})),
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError, ApprovalError) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 2

    print(json.dumps({"success": True, "request": asdict(request)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
