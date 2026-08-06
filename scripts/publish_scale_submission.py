#!/usr/bin/env python3
"""Validate a local scale result and publish its compact dashboard aggregate."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runner.scale_submission import (  # noqa: E402
    build_dashboard_document,
    file_sha256,
    load_json,
    publish_dashboard_document,
    validate_submission,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path)
    parser.add_argument("--fission-version", required=True)
    parser.add_argument("--source-asset", required=True)
    parser.add_argument("--source-sha256")
    parser.add_argument(
        "--lock",
        type=Path,
        default=ROOT / "corpus" / "scale" / "dataset-lock.json",
    )
    parser.add_argument("--public-root", type=Path, default=ROOT / "public")
    parser.add_argument("--min-clean-coverage", type=float, default=0.5)
    args = parser.parse_args()

    actual_sha256 = file_sha256(args.submission)
    if args.source_sha256 and args.source_sha256.lower() != actual_sha256:
        parser.error(
            f"submission sha256 {actual_sha256} does not match "
            f"{args.source_sha256.lower()}"
        )
    envelope = load_json(args.submission)
    lock = json.loads(args.lock.read_text(encoding="utf-8"))
    validation = validate_submission(
        envelope,
        lock,
        expected_version=args.fission_version,
        min_clean_coverage=args.min_clean_coverage,
    )
    document = build_dashboard_document(
        envelope,
        validation,
        source_asset=args.source_asset,
        source_sha256=actual_sha256,
    )
    paths = publish_dashboard_document(document, args.public_root)
    print(
        f"Validated {validation['subjects']:,} subjects / "
        f"{validation['rows']:,} rows for {validation['version']}"
    )
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
