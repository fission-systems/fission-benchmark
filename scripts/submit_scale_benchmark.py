#!/usr/bin/env python3
"""Package a local scale envelope and optionally submit it for CI publication."""
from __future__ import annotations

import argparse
import gzip
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runner.scale_submission import (  # noqa: E402
    file_sha256,
    load_json,
    normalize_version,
    validate_submission,
)

DEFAULT_REPOSITORY = "fission-systems/fission-benchmark"


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path)
    parser.add_argument("--fission-version", required=True)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument(
        "--lock",
        type=Path,
        default=ROOT / "corpus" / "scale" / "dataset-lock.json",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / ".cache" / "scale-submissions"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Upload the release asset and dispatch the publication workflow.",
    )
    args = parser.parse_args()

    envelope = load_json(args.submission)
    lock = json.loads(args.lock.read_text(encoding="utf-8"))
    version = normalize_version(args.fission_version)
    validation = validate_submission(
        envelope, lock, expected_version=version, min_clean_coverage=0.5
    )
    run_id = validation["run_id"]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    asset_name = f"fission-unofficial-decbench-{version}-{run_id}.json.gz"
    asset_path = args.output_dir / asset_name
    if asset_path.resolve() == args.submission.resolve():
        parser.error("submission and packaged asset paths must differ")
    source_handle = (
        gzip.open(args.submission, "rb")
        if args.submission.suffix == ".gz"
        else args.submission.open("rb")
    )
    with source_handle as source, asset_path.open("wb") as raw_output:
        with gzip.GzipFile(
            filename="", mode="wb", fileobj=raw_output, mtime=0
        ) as output:
            shutil.copyfileobj(source, output)
    sha256 = file_sha256(asset_path)
    release_tag = f"benchmark-{version}"

    print(f"Validated {validation['subjects']:,} subjects / {validation['rows']:,} rows")
    print(f"Asset: {asset_path}")
    print(f"SHA-256: {sha256}")
    commands = [
        [
            "gh",
            "release",
            "upload",
            release_tag,
            str(asset_path),
            "--repo",
            args.repository,
        ],
        [
            "gh",
            "workflow",
            "run",
            "publish-unofficial-corpus.yml",
            "--repo",
            args.repository,
            "-f",
            f"release_tag={release_tag}",
            "-f",
            f"asset_name={asset_name}",
            "-f",
            f"sha256={sha256}",
            "-f",
            f"fission_version={version}",
        ],
    ]
    if args.execute:
        if shutil.which("gh") is None:
            parser.error("gh CLI is required with --execute")
        for command in commands:
            _run(command)
    else:
        print("Dry run; add --execute to run:")
        for command in commands:
            print("  " + " ".join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
