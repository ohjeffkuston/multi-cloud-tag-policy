"""Command-line interface for the tag policy auditor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .engine import audit_inventory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit AWS, Azure, and GCP resource tags without changing resources.")
    parser.add_argument("inventory", type=Path, help="Path to an inventory JSON file")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = json.loads(args.inventory.read_text(encoding="utf-8"))
    report = audit_inventory(payload)
    print(json.dumps(report, indent=None if args.compact else 2, sort_keys=True))
    return {"PASS": 0, "REVIEW": 1, "BLOCK": 2}[report["decision"]]

